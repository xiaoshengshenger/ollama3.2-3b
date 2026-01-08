export interface CodeValidateResult {
  package_type: number;
  package_name: string;
  max_queries: number;
  allowed_models: string[];
  expire_time: string;
  file_limit_mb: number;
  db_limit_gb: number;
  is_valid: boolean;
}