export interface CodeValidateResult {
    days: number;
    maxQueries: number;
    allowedModels: string[];
    fileSizeLimit: number;
    dbSizeLimit: number;
    package: string;
  }