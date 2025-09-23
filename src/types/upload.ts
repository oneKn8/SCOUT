export interface UploadResponse {
  resume_id: string;
  run_id: string;
  file_hash: string;
  stored_path: string;
  file_name: string;
  file_size: number;
  mime_type: string;
  upload_timestamp: string;
  status: string;
}

export interface ErrorResponse {
  error: string;
  message: string;
  request_id: string;
  details?: Record<string, any>;
}

export interface FileValidation {
  isValid: boolean;
  errors: string[];
}

export interface UploadState {
  isUploading: boolean;
  uploadResult: UploadResponse | null;
  error: string | null;
}

export const ALLOWED_FILE_TYPES = [".pdf", ".docx"] as const;
export const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB

export type AllowedFileType = typeof ALLOWED_FILE_TYPES[number];