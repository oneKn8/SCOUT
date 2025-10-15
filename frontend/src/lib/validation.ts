import { FileValidation, ALLOWED_FILE_TYPES, MAX_FILE_SIZE } from "@/types/upload";
import { getFileExtension } from "./utils";

export function validateFile(file: File): FileValidation {
  const errors: string[] = [];

  // Check file type
  const extension = `.${getFileExtension(file.name).toLowerCase()}`;
  if (!ALLOWED_FILE_TYPES.includes(extension as any)) {
    errors.push(
      `File type "${extension}" is not supported. Please upload ${ALLOWED_FILE_TYPES.join(
        " or "
      )} files.`
    );
  }

  // Check file size
  if (file.size > MAX_FILE_SIZE) {
    const maxSizeMB = Math.round(MAX_FILE_SIZE / (1024 * 1024));
    const fileSizeMB = Math.round(file.size / (1024 * 1024));
    errors.push(
      `File size (${fileSizeMB}MB) exceeds the maximum limit of ${maxSizeMB}MB.`
    );
  }

  // Check if file is empty
  if (file.size === 0) {
    errors.push("File appears to be empty. Please select a valid file.");
  }

  return {
    isValid: errors.length === 0,
    errors,
  };
}

export function validateMultipleFiles(files: File[]): FileValidation {
  const errors: string[] = [];

  if (files.length === 0) {
    errors.push("Please select at least one file.");
    return { isValid: false, errors };
  }

  if (files.length > 1) {
    errors.push("Please select only one file at a time.");
    return { isValid: false, errors };
  }

  // Validate the single file
  return validateFile(files[0]);
}