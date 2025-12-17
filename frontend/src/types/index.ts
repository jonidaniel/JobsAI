/**
 * Shared TypeScript type definitions for the JobsAI frontend
 */

/**
 * Form data value types - can be string, number, or array of strings
 */
export type FormDataValue = string | number | string[];

/**
 * Form data structure - flat key-value pairs
 */
export type FormData = Record<string, FormDataValue>;

/**
 * Validation errors - maps field keys to error messages
 */
export type ValidationErrors = Record<string, string>;

/**
 * Validation result
 */
export interface ValidationResult {
  isValid: boolean;
  errors: ValidationErrors;
}

/**
 * Grouped form data item - single key-value pair in an object
 */
export type GroupedFormDataItem = Record<string, FormDataValue>;

/**
 * Grouped form data - organized by question set name
 */
export type GroupedFormData = Record<string, GroupedFormDataItem[]>;

/**
 * Download info for cover letters
 */
export interface DownloadInfo {
  jobId: string;
  filenames: string[];
}

/**
 * Pipeline progress phase
 */
export type PipelinePhase =
  | "profiling"
  | "searching"
  | "scoring"
  | "analyzing"
  | "generating";

/**
 * Pipeline status
 */
export type PipelineStatus = "running" | "complete" | "error" | "cancelled";

/**
 * Progress response from API
 */
export interface ProgressResponse {
  job_id: string;
  status: PipelineStatus;
  progress?: {
    phase: PipelinePhase;
    message: string;
  };
  has_progress?: boolean;
  filenames?: string[];
  filename?: string;
  error?: string;
}
