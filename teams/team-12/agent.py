# -*- coding: utf-8 -*-
"""
Autonomous Cleaning Agent for DataCleanAgent.
Integrates ReAct loop with Google Gemini 2.5 Flash.
Decoupled from unsafe exec() calls; operates via action_registry.py.
"""

import os
import re
import time
import json
import requests
import traceback
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Tuple, Generator, Optional

from action_registry import execute_action, get_action_python_code, ACTION_REGISTRY

class CleaningAgent:
    """
    Autonomous ReAct (Reason-Act-Observe) cleaning agent.
    Coordinates data restoration steps using either AI (Gemini) or Heuristics.
    Runs actions from the secure Action Registry, eliminating arbitrary code execution.
    Supports multi-step transaction rollback.
    """
    
    def __init__(self, df: pd.DataFrame, initial_profile: Dict[str, Any], mode: str = "genai"):
        self.initial_profile = initial_profile
        self.mode = mode
        self.step_count = 0
        self.chat_history: List[Dict[str, Any]] = []
        
        # DataFrame and history storage for rollback support
        self.df = df.copy()
        self.df_history: List[pd.DataFrame] = [df.copy()]
        self.action_log: List[Dict[str, Any]] = []

    def rollback_last_step(self) -> Tuple[bool, str]:
        """
        Reverts the last successfully executed action.
        Returns: (success, message)
        """
        if len(self.df_history) <= 1:
            return False, "Cannot rollback: already at the initial dataset state."
            
        if not self.action_log:
            return False, "No cleaning actions recorded in the log."
            
        # Pop last state and action
        self.df_history.pop()
        self.df = self.df_history[-1].copy()
        removed_action = self.action_log.pop()
        
        # Pop Gemini history steps if running in GenAI mode
        if self.mode == "genai" and len(self.chat_history) >= 2:
            # Pop model response and user observation
            self.chat_history.pop()
            self.chat_history.pop()
            
        self.step_count = max(0, self.step_count - 1)
        
        msg = f"Rolled back step {removed_action.get('step', '')}: '{removed_action.get('justification', '')}'."
        return True, msg

    def _execute_action_safely(self, action_name: str, action_args: Dict[str, Any]) -> Tuple[pd.DataFrame, bool, str, str]:
        """
        Executes a registered action on a copy of the dataframe.
        Returns: (new_df, success, error_message, description)
        """
        result = execute_action(action_name, self.df, **action_args)
        if result.success:
            return result.df, True, "", result.description
        else:
            err = result.error_message or "Unknown execution error."
            return self.df, False, err, result.description or err

    def _call_gemini(self) -> Dict[str, Any]:
        """Helper to make structured API calls to Gemini 2.5 Flash."""
        api_key = os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY environment variable is missing. Please configure it in the sidebar.")
            
        url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash:generateContent"
        
        contents = []
        for msg in self.chat_history:
            contents.append({
                "role": msg["role"],
                "parts": [{"text": msg["content"]}]
            })
            
        # Define JSON response schema matching selected actions
        schema = {
            "type": "OBJECT",
            "properties": {
                "thought": {
                    "type": "STRING",
                    "description": "Step-by-step reasoning explaining why you are prioritizing this specific data issue and which registry action matches."
                },
                "action_name": {
                    "type": "STRING",
                    "enum": list(ACTION_REGISTRY.keys()),
                    "description": "The exact name of the cleaning action strategy to execute."
                },
                "action_args": {
                    "type": "OBJECT",
                    "properties": {
                        "column": {
                            "type": "STRING",
                            "description": "The name of a single target column (e.g., 'Age', 'Fare', 'Sex', 'Survived')."
                        },
                        "columns": {
                            "type": "ARRAY",
                            "items": {"type": "STRING"},
                            "description": "A list of target column names (e.g., ['Cabin']). Never output an empty list."
                        },
                        "group_cols": {
                            "type": "ARRAY",
                            "items": {"type": "STRING"},
                            "description": "Grouping columns used for median imputation (e.g., ['Pclass', 'Sex'])."
                        },
                        "threshold": {
                            "type": "NUMBER",
                            "description": "Missingness threshold for dropping columns, between 0.0 and 1.0."
                        },
                        "subset": {
                            "type": "ARRAY",
                            "items": {"type": "STRING"},
                            "description": "Subset of columns to look at for duplicate rows (e.g., ['PassengerId'])."
                        },
                        "keep": {
                            "type": "STRING",
                            "description": "Standard keep policy for duplicate removal: 'first', 'last', or false."
                        },
                        "multiplier": {
                            "type": "NUMBER",
                            "description": "IQR multiplier for outlier clamping (e.g., 1.5 or 3.0)."
                        },
                        "placeholder": {
                            "type": "STRING",
                            "description": "The static placeholder value to fill in remaining nulls (e.g., 'Unknown')."
                        },
                        "allowed_values": {
                            "type": "ARRAY",
                            "items": {"type": "STRING"},
                            "description": "List of allowed categorical values for validation (e.g., ['0', '1'])."
                        },
                        "min_val": {
                            "type": "NUMBER",
                            "description": "Minimum valid range bound for validation (e.g., 0)."
                        },
                        "max_val": {
                            "type": "NUMBER",
                            "description": "Maximum valid range bound for validation (e.g., 120)."
                        }
                    },
                    "description": "Arguments matching the selected registered action. Only populate the keys required for the chosen action."
                },
                "justification": {
                    "type": "STRING",
                    "description": "A concise, user-friendly statistical justification of the action taken."
                },
                "status": {
                    "type": "STRING",
                    "enum": ["continue", "done"],
                    "description": "Set to 'continue' if there are more issues to fix, or 'done' if you have resolved all issues."
                }
            },
            "required": ["thought", "action_name", "action_args", "justification", "status"]
        }
        
        payload = {
            "contents": contents,
            "generationConfig": {
                "temperature": 0.1,
                "responseMimeType": "application/json",
                "responseSchema": schema
            }
        }
        
        max_retries = 5
        for attempt in range(max_retries):
            try:
                headers = {
                    "Content-Type": "application/json",
                    "x-goog-api-key": api_key
                }
                response = requests.post(url, json=payload, headers=headers, timeout=60)
                if response.status_code == 200:
                    res_json = response.json()
                    text = res_json['candidates'][0]['content']['parts'][0]['text']
                    return json.loads(text)
                elif response.status_code == 429:
                    sleep_time = (2 ** attempt) + 2
                    time.sleep(sleep_time)
                else:
                    raise Exception(f"Gemini API returned status code {response.status_code}: {response.text}")
            except Exception as e:
                if attempt == max_retries - 1:
                    raise e
                time.sleep(2)
                
        raise Exception("Failed to contact Gemini API after multiple retries.")

    def _get_heuristic_action(self) -> Dict[str, Any]:
        """
        Determines the next cleaning action based on statistical heuristics.
        Returns structured registry actions rather than raw Python code.
        """
        # 1. Uniqueness check (Duplicates)
        # Identify key/index columns
        id_cols = [c for c in self.df.columns if c.lower() in ['passengerid', 'id', 'uuid', 'index']]
        df_for_dup = self.df.drop(columns=id_cols) if id_cols else self.df
        if df_for_dup.duplicated().sum() > 0:
            return {
                "thought": "Found exact duplicate records after excluding identifier columns. Running duplicate removal action.",
                "action_name": "remove_duplicates",
                "action_args": {"subset": [c for c in self.df.columns if c not in id_cols]},
                "justification": "Removed exact duplicate records from the dataset, retaining only the first occurrence.",
                "status": "continue"
            }

        # 2. Categorical labels consistency check
        for col, mapping in self.initial_profile.get("inconsistent_groups", {}).items():
            if col in self.df.columns and self.df[col].isin(mapping.keys()).any():
                return {
                    "thought": f"Fuzzy grouping detected inconsistent spelling/casing text representations in column '{col}'. Normalizing to dominant value.",
                    "action_name": "normalize_categories",
                    "action_args": {"column": col, "mapping": mapping},
                    "justification": f"Standardized inconsistent spelling/casing categories in column '{col}'.",
                    "status": "continue"
                }

        # 3. Validity range boundaries check
        # Survived validity (Must be 0 or 1)
        if 'Survived' in self.df.columns:
            bad_survived = ~self.df['Survived'].dropna().astype(str).str.strip().str.replace('.0', '', regex=False).isin(['0', '1'])
            if bad_survived.any():
                return {
                    "thought": "Found invalid non-binary values in 'Survived' column. Coercing and replacing invalid values.",
                    "action_name": "replace_invalid_values",
                    "action_args": {"column": "Survived", "allowed_values": [0, 1]},
                    "justification": "Coerced and replaced invalid Survived values outside standard binary levels [0, 1] with NaN.",
                    "status": "continue"
                }

        # Pclass validity (Must be 1, 2, 3)
        if 'Pclass' in self.df.columns:
            bad_pclass = ~self.df['Pclass'].dropna().astype(str).str.strip().str.replace('.0', '', regex=False).isin(['1', '2', '3'])
            if bad_pclass.any():
                return {
                    "thought": "Found invalid class categories in 'Pclass' column. Coercing and replacing invalid values.",
                    "action_name": "replace_invalid_values",
                    "action_args": {"column": "Pclass", "allowed_values": [1, 2, 3]},
                    "justification": "Coerced and replaced invalid Pclass levels outside [1, 2, 3] with NaN.",
                    "status": "continue"
                }

        # Age validity (Must be between 0 and 120)
        if 'Age' in self.df.columns:
            numeric_age = pd.to_numeric(self.df['Age'], errors='coerce')
            bad_age = (numeric_age < 0) | (numeric_age > 120)
            if bad_age.any():
                return {
                    "thought": "Found negative or unrealistic values in 'Age'. Coercing and replacing invalid values.",
                    "action_name": "replace_invalid_values",
                    "action_args": {"column": "Age", "min_val": 0, "max_val": 120},
                    "justification": "Coerced negative or extreme Age entries outside range [0, 120] to NaN.",
                    "status": "continue"
                }

        # Fare validity (Must be >= 0)
        if 'Fare' in self.df.columns:
            numeric_fare = pd.to_numeric(self.df['Fare'], errors='coerce')
            bad_fare = numeric_fare < 0
            if bad_fare.any():
                return {
                    "thought": "Found negative fares in 'Fare' column. Coercing and replacing invalid values.",
                    "action_name": "replace_invalid_values",
                    "action_args": {"column": "Fare", "min_val": 0},
                    "justification": "Coerced negative Fare entries outside logical limit [0, inf) to NaN.",
                    "status": "continue"
                }

        # 4. Completeness check (Imputing missing values)
        null_cols = self.df.columns[self.df.isna().any()].tolist()
        if null_cols:
            col = null_cols[0]
            col_info = self.initial_profile["columns"].get(col, {})
            inferred_type = col_info.get("inferred_type", "Categorical")
            null_pct = col_info.get("null_pct", 0)
            
            if inferred_type == "Numeric":
                # Check if we can perform grouped median imputation as a sophisticated fallback
                # If we have Pclass and Sex, do grouped median imputer
                if col.lower() == 'age' and 'pclass' in self.df.columns and 'sex' in self.df.columns:
                    return {
                        "thought": f"Imputing missing values in numerical column '{col}' using advanced grouped medians by Pclass and Sex.",
                        "action_name": "grouped_median_imputation",
                        "action_args": {"column": col, "group_cols": ["Pclass", "Sex"]},
                        "justification": f"Imputed missing '{col}' values using sub-group medians (Pclass & Sex) to preserve distribution variances.",
                        "status": "continue"
                    }
                else:
                    return {
                        "thought": f"Imputing missing values in numerical column '{col}' with its median value.",
                        "action_name": "median_imputation",
                        "action_args": {"column": col},
                        "justification": f"Imputed missing values in numerical column '{col}' with the median.",
                        "status": "continue"
                    }
            elif null_pct > 50:
                # Fill highly sparse categorical column with placeholder
                return {
                    "thought": f"Column '{col}' is highly sparse ({null_pct:.1f}% missing). Filling nulls with 'Unknown' placeholder.",
                    "action_name": "fill_placeholders",
                    "action_args": {"column": col, "placeholder": "Unknown"},
                    "justification": f"Filled highly sparse categorical column '{col}' with 'Unknown' placeholder to prevent data bias.",
                    "status": "continue"
                }
            else:
                # Fill categorical column with mode
                return {
                    "thought": f"Imputing missing values in categorical column '{col}' with its mode.",
                    "action_name": "mode_imputation",
                    "action_args": {"column": col},
                    "justification": f"Imputed missing categorical entries in '{col}' with the column mode.",
                    "status": "continue"
                }

        # 5. Outliers check (IQR clamping)
        already_clamped = set()
        for act in self.action_log:
            just = act.get('justification', '')
            if "Clamped" in just:
                match = re.search(r"column '([^']+)'", just)
                if match:
                    already_clamped.add(match.group(1))

        for col in self.df.columns:
            if col in already_clamped or col.lower() in id_cols:
                continue
            col_info = self.initial_profile["columns"].get(col, {})
            if col_info.get("inferred_type") == 'Numeric':
                # Check for outliers
                series = pd.to_numeric(self.df[col], errors='coerce')
                q25 = series.quantile(0.25)
                q75 = series.quantile(0.75)
                iqr = q75 - q25
                mult = 5.0 if col.lower() == 'fare' else 3.0
                upper_limit = q75 + mult * iqr
                lower_limit = q25 - mult * iqr
                
                outliers = (series > upper_limit) | (series < lower_limit)
                if outliers.any():
                    return {
                        "thought": f"Column '{col}' contains statistical outliers outside {mult}*IQR bounds. Clamping boundaries.",
                        "action_name": "clamp_iqr_outliers",
                        "action_args": {"column": col, "multiplier": mult},
                        "justification": f"Clamped extreme statistical outliers in column '{col}' to stable statistical boundaries.",
                        "status": "continue"
                    }

        # 6. Fallback if no issues remain
        return {
            "thought": "All duplicate rows, categorical inconsistencies, out-of-bounds cells, missing values, and outliers have been resolved. Restorations complete.",
            "action_name": "remove_duplicates", # dummy done action
            "action_args": {},
            "justification": "All identified data quality defects resolved.",
            "status": "done"
        }

    def run_cleaning_step(self) -> Generator[Dict[str, Any], None, None]:
        """
        Executes a single step of the agent's cleaning process.
        Yields status dictionaries for the Streamlit UI to display.
        """
        self.step_count += 1
        
        # 1. Initialize system prompt and observations in GenAI mode
        if self.mode == "genai" and not self.chat_history:
            system_prompt = self._get_system_prompt()
            initial_observation = self._get_initial_observation()
            self.chat_history.append({"role": "user", "content": f"{system_prompt}\n\nHere is the initial dataset profile and sample data:\n{initial_observation}"})
            
        yield {"status": "thinking", "step": self.step_count, "message": "Analyzing data quality profile and planning next action..."}
        
        # Rate limit safety delay
        time.sleep(1.2)
        
        try:
            # 2. Retrieve thought/action from appropriate engine
            if self.mode == "genai":
                agent_response = self._call_gemini()
            else:
                agent_response = self._get_heuristic_action()
                
            thought = agent_response.get("thought", "")
            action_name = agent_response.get("action_name", "")
            action_args = agent_response.get("action_args", {})
            justification = agent_response.get("justification", "")
            status = agent_response.get("status", "continue")
            
            # Generate equivalent python code string to keep app.py and reports compatible
            equivalent_code = get_action_python_code(action_name, **action_args) if status != "done" else ""
            
            if status == "done":
                yield {
                    "status": "completed",
                    "step": self.step_count,
                    "message": "Agent has completed all cleaning tasks.",
                    "thought": thought,
                    "justification": "Initial profiling is clean, or all issues resolved.",
                    "code": ""
                }
                return
                
            yield {
                "status": "executing",
                "step": self.step_count,
                "thought": thought,
                "code": equivalent_code,
                "justification": justification,
                "message": f"Executing registered action '{action_name}' in sandbox..."
            }
            
            # 3. Action Registry execution (replaces raw exec retry loop)
            success = False
            error_message = ""
            current_action_name = action_name
            current_action_args = action_args
            
            max_attempts = 3 if self.mode == "genai" else 1
            for attempt in range(max_attempts):
                new_df, success, error_message, _ = self._execute_action_safely(current_action_name, current_action_args)
                
                if success:
                    # Verify if DataFrame actually changed
                    if self.df.equals(new_df):
                        success = False
                        error_message = f"Action '{current_action_name}' succeeded but did not modify the DataFrame. Check arguments."
                    else:
                        break
                        
                if self.mode == "genai":
                    yield {
                        "status": "healing",
                        "step": self.step_count,
                        "attempt": attempt + 1,
                        "error": error_message,
                        "message": f"Action execution failed. Retrying with auto-correction (Attempt {attempt + 1}/3)..."
                    }
                    
                    time.sleep(2.0)
                    
                    # Feed execution error back to Gemini for self-healing
                    heal_message = {
                        "role": "user",
                        "content": f"The action '{current_action_name}' failed on attempt {attempt + 1} with error:\n{error_message}\n\nPlease analyze, select a correct action or arguments, and return a corrected JSON object."
                    }
                    temp_history = self.chat_history.copy()
                    temp_history.append({"role": "model", "content": json.dumps(agent_response)})
                    temp_history.append(heal_message)
                    self.chat_history = temp_history
                    
                    agent_response = self._call_gemini()
                    thought = agent_response.get("thought", "")
                    current_action_name = agent_response.get("action_name", "")
                    current_action_args = agent_response.get("action_args", {})
                    justification = agent_response.get("justification", "")
                    equivalent_code = get_action_python_code(current_action_name, **current_action_args)
                    
                    yield {
                        "status": "executing",
                        "step": self.step_count,
                        "thought": thought,
                        "code": equivalent_code,
                        "justification": justification,
                        "message": f"Executing self-healed action '{current_action_name}' in sandbox..."
                    }
            
            if success:
                # 4. Save state changes
                original_cols = set(self.df.columns)
                new_cols = set(new_df.columns)
                
                # Update DataFrame and historical stack
                self.df = new_df
                self.df_history.append(new_df.copy())
                
                action_record = {
                    "step": self.step_count,
                    "thought": thought,
                    "code": equivalent_code, # keep for logs and exports
                    "action_name": current_action_name,
                    "action_args": current_action_args,
                    "justification": justification,
                    "columns_added": list(new_cols - original_cols),
                    "columns_removed": list(original_cols - new_cols),
                    "shape_after": self.df.shape
                }
                self.action_log.append(action_record)
                
                if self.mode == "genai":
                    self.chat_history.append({"role": "model", "content": json.dumps(agent_response)})
                    observation = f"Step successful. Action applied. Current dataset shape: {self.df.shape}."
                    self.chat_history.append({"role": "user", "content": observation})
                    
                yield {
                    "status": "success",
                    "step": self.step_count,
                    "message": f"Successfully executed action: {justification}",
                    "df": self.df,
                    "action": action_record
                }
            else:
                fail_record = {
                    "step": self.step_count,
                    "thought": thought,
                    "code": equivalent_code,
                    "action_name": current_action_name,
                    "action_args": current_action_args,
                    "justification": f"[FAILED] Action failed: {justification}",
                    "error": error_message
                }
                self.action_log.append(fail_record)
                
                if self.mode == "genai":
                    self.chat_history.append({"role": "model", "content": json.dumps(agent_response)})
                    observation = f"Step failed completely after 3 attempts with error: {error_message}. Do NOT repeat this action. Try other issues or set status to 'done'."
                    self.chat_history.append({"role": "user", "content": observation})
                    
                yield {
                    "status": "failed",
                    "step": self.step_count,
                    "message": f"Failed to execute action: {error_message}",
                    "action": fail_record
                }
                
        except Exception as e:
            yield {
                "status": "api_error",
                "step": self.step_count,
                "message": f"An error occurred in the execution engine: {str(e)}"
            }

    def _get_system_prompt(self) -> str:
        """Returns the system instruction prompt detailing registered actions."""
        actions_desc = ""
        for name, instance in ACTION_REGISTRY.items():
            actions_desc += f"- **{name}**: {instance.__doc__.strip()}\n"
            
        template = r"""You are the AI brain of DataCleanAgent, a production-grade autonomous data cleaning system.
Your goal is to inspect a statistical profile and sample of a dataset, reason about quality defects, and select the optimal deterministic action from our registered suite.

You are NOT allowed to write raw Python code. You must select one of our pre-defined registered actions:
{actions_desc}

Supported Actions & Arguments mapping:
1. `median_imputation`: imputes missing values in a numeric column with its median.
   Args: { "column": "ColName" }
2. `grouped_median_imputation`: imputes missing values in a numeric column using grouped medians from grouping columns.
   Args: { "column": "ColName", "group_cols": ["GrpCol1", "GrpCol2"] }
3. `mode_imputation`: imputes missing values in a categorical column with its mode.
   Args: { "column": "ColName" }
4. `drop_columns`: drops specified columns or columns exceeding a missingness threshold.
   Args: { "columns": ["ColName1", "ColName2"] } or { "threshold": 0.7 } (at least one of 'columns' list or 'threshold' must be specified. For example, if you want to drop 'Cabin', specify: { "columns": ["Cabin"] })
5. `remove_duplicates`: removes exact duplicate rows based on subset columns.
   Args: { "subset": ["ColName1", "ColName2"], "keep": "first" } (subset and keep are optional)
6. `normalize_categories`: normalizes variations of labels using fuzzy matches or custom dictionary.
   Args: { "column": "ColName", "mapping": {"M": "male", "Male": "male"} } (mapping is optional)
7. `clamp_iqr_outliers`: clips outliers outside IQR boundaries.
   Args: { "column": "ColName", "multiplier": 1.5 } (optional multiplier, default is 1.5)
8. `coerce_numeric`: coerces text columns to numeric, replacing unparseable cells with NaN.
   Args: { "column": "ColName" }
9. `coerce_boolean`: standardizes yes/no, true/false, 1/0 columns to standard integers [0, 1].
   Args: { "column": "ColName" }
10. `drop_constant_columns`: drops zero-variance/constant columns.
    Args: {}
11. `clamp_negative_values`: clamps negative numeric values to 0.0.
    Args: { "column": "ColName" }
12. `fill_placeholders`: fills remaining missing values in a column with a static placeholder.
    Args: { "column": "ColName", "placeholder": "Unknown" }
13. `replace_invalid_values`: replaces values not in an allowed list or outside numeric range bounds with NaN or fallback.
    Args: { "column": "ColName", "allowed_values": ["0", "1"], "min_val": 0, "max_val": 120, "replace_with": null } (allowed_values, min_val, max_val are optional)

Rules of Operation:
1. Every step must be atomic. Focus on one issue or column per step.
2. Select actions that resolve issues identified in the "detected_issues" log.
3. Use `replace_invalid_values` to handle categorical values out of range (like Survived not in [0,1] or Pclass not in [1,2,3]) or numeric values out of logical bounds (like Age > 120 or Age < 0) before running imputer steps.
4. When you believe the dataset has been fully cleaned (all missingness, duplicates, outliers, inconsistencies, invalid values resolved), set 'status' to 'done' and 'action_name' to 'remove_duplicates'.
5. Never output empty lists `[]` for `columns` argument in `drop_columns` if you intend to drop specific columns. You must include the actual column name string(s) inside the list, e.g., `{"columns": ["Cabin"]}`.
6. For all list arguments like `columns` or `subset`, you must provide a list containing actual column names from the dataset.

Your response must be a JSON object adhering to the schema. Keep thoughts concise and justifications clear.
"""
        return template.replace("{actions_desc}", actions_desc)

    def _get_initial_observation(self) -> str:
        """Serializes the dataset profile and sample data into a compact text format for the Gemini context window."""
        summary = self.initial_profile["summary"]
        dimensions = self.initial_profile["dimension_scores"]
        
        columns_info = {}
        for col, info in self.initial_profile["columns"].items():
            col_data = {
                "dtype": info["dtype"],
                "inferred_type": info["inferred_type"],
                "nulls": f"{info['null_count']} ({info['null_pct']:.1f}%)",
                "uniques": info["unique_count"]
            }
            if info.get("min") is not None:
                col_data.update({
                    "min": info["min"],
                    "max": info["max"],
                    "median": info.get("median")
                })
            if info.get("top_values") is not None:
                col_data["top_values"] = info["top_values"]
            columns_info[col] = col_data
            
        sample_rows = self.df.head(5).to_dict(orient="records")
        
        payload = {
            "dataset_summary": {
                "shape": [summary["rows"], summary["columns"]],
                "duplicate_rows": summary["duplicate_rows"]
            },
            "dimension_scores": dimensions,
            "column_profiles": columns_info,
            "detected_issues": [
                {
                    "dim": iss["dimension"],
                    "col": iss["column"],
                    "severity": iss["severity"],
                    "desc": iss["description"]
                }
                for iss in self.initial_profile["issues"]
            ],
            "categorical_inconsistencies": self.initial_profile["inconsistent_groups"],
            "sample_rows_head": sample_rows
        }
        
        return json.dumps(payload, indent=2)
