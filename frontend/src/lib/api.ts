import { UploadResponse, ErrorResponse } from "@/types/upload";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || (typeof window !== 'undefined' ? `${window.location.protocol}//${window.location.hostname}:8000` : "http://localhost:8000");

export class ApiError extends Error {
  constructor(
    message: string,
    public statusCode: number,
    public details?: any
  ) {
    super(message);
    this.name = "ApiError";
  }
}

export async function uploadResume(file: File): Promise<UploadResponse> {
  const formData = new FormData();
  formData.append("file", file);

  try {
    const response = await fetch(`${API_BASE_URL}/api/uploads/resume`, {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      const errorData: ErrorResponse = await response.json();
      throw new ApiError(
        errorData.message || "Upload failed",
        response.status,
        errorData
      );
    }

    const result: UploadResponse = await response.json();
    return result;
  } catch (error) {
    if (error instanceof ApiError) {
      throw error;
    }

    // Handle network errors or other unexpected errors
    throw new ApiError(
      "Network error occurred. Please check your connection and try again.",
      0
    );
  }
}

export async function checkApiHealth(): Promise<{ status: string }> {
  try {
    const response = await fetch(`${API_BASE_URL}/health`);
    if (!response.ok) {
      throw new Error("Health check failed");
    }
    return await response.json();
  } catch (error) {
    throw new ApiError("API health check failed", 0);
  }
}