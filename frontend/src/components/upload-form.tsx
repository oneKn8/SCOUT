"use client";

import React, { useState, useCallback, useRef } from "react";
import { Upload, FileText, CheckCircle, AlertCircle, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { useToast } from "@/hooks/use-toast";
import { validateMultipleFiles } from "@/lib/validation";
import { uploadResume, ApiError } from "@/lib/api";
import { formatFileSize, generateFileHash } from "@/lib/utils";
import { UploadResponse, UploadState, ALLOWED_FILE_TYPES, MAX_FILE_SIZE } from "@/types/upload";
import { UploadResult } from "./upload-result";

interface UploadFormProps {
  onUploadSuccess?: (result: UploadResponse) => void;
}

export function UploadForm({ onUploadSuccess }: UploadFormProps) {
  const [uploadState, setUploadState] = useState<UploadState>({
    isUploading: false,
    uploadResult: null,
    error: null,
  });
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [fileHash, setFileHash] = useState<string>("");
  const [dragActive, setDragActive] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const dropzoneRef = useRef<HTMLDivElement>(null);
  const { toast } = useToast();

  const resetForm = useCallback(() => {
    setSelectedFile(null);
    setFileHash("");
    setUploadState({
      isUploading: false,
      uploadResult: null,
      error: null,
    });
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  }, []);

  const handleFileSelection = useCallback(async (files: File[]) => {
    const validation = validateMultipleFiles(files);

    if (!validation.isValid) {
      const errorMessage = validation.errors.join(" ");
      setUploadState(prev => ({ ...prev, error: errorMessage }));
      toast({
        variant: "destructive",
        title: "File Validation Error",
        description: errorMessage,
      });
      return;
    }

    const file = files[0];
    setSelectedFile(file);
    setUploadState(prev => ({ ...prev, error: null }));

    // Generate file hash for display
    try {
      const hash = await generateFileHash(file);
      setFileHash(hash);
    } catch (error) {
      console.error("Failed to generate file hash:", error);
      setFileHash("Unable to calculate");
    }

    toast({
      title: "File Selected",
      description: `${file.name} (${formatFileSize(file.size)}) is ready for upload.`,
    });
  }, [toast]);

  const handleDrop = useCallback((e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const files = Array.from(e.dataTransfer.files);
      handleFileSelection(files);
    }
  }, [handleFileSelection]);

  const handleDragOver = useCallback((e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
  }, []);

  const handleFileInputChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      const files = Array.from(e.target.files);
      handleFileSelection(files);
    }
  }, [handleFileSelection]);

  const handleSubmit = useCallback(async () => {
    if (!selectedFile) {
      toast({
        variant: "destructive",
        title: "No File Selected",
        description: "Please select a file before uploading.",
      });
      return;
    }

    setUploadState(prev => ({ ...prev, isUploading: true, error: null }));

    try {
      const result = await uploadResume(selectedFile);
      setUploadState({
        isUploading: false,
        uploadResult: result,
        error: null,
      });

      // Call the success callback if provided
      if (onUploadSuccess) {
        onUploadSuccess(result);
      }

      toast({
        title: "Upload Successful",
        description: `${selectedFile.name} has been uploaded successfully.`,
      });
    } catch (error) {
      let errorMessage = "Upload failed. Please try again.";

      if (error instanceof ApiError) {
        errorMessage = error.message;
      }

      setUploadState({
        isUploading: false,
        uploadResult: null,
        error: errorMessage,
      });

      toast({
        variant: "destructive",
        title: "Upload Failed",
        description: errorMessage,
      });
    }
  }, [selectedFile, toast, onUploadSuccess]);

  const handleKeyDown = useCallback((e: React.KeyboardEvent<HTMLDivElement>) => {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      fileInputRef.current?.click();
    }
  }, []);

  // Show upload result if upload was successful
  if (uploadState.uploadResult) {
    return <UploadResult result={uploadState.uploadResult} onStartOver={resetForm} />;
  }

  return (
    <div className="w-full max-w-2xl mx-auto space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Upload className="h-5 w-5" />
            Upload Resume
          </CardTitle>
          <CardDescription>
            Select a PDF or DOCX file (max {formatFileSize(MAX_FILE_SIZE)}) to get started.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* File Dropzone */}
          <div
            ref={dropzoneRef}
            className={`
              relative border-2 border-dashed rounded-lg p-8 text-center cursor-pointer
              transition-colors duration-200 focus-within:ring-2 focus-within:ring-ring focus-within:ring-offset-2
              ${dragActive
                ? "border-primary bg-primary/5"
                : selectedFile
                  ? "border-green-500 bg-green-50 dark:bg-green-950/20"
                  : "border-muted-foreground/25 hover:border-muted-foreground/50"
              }
            `}
            onDrop={handleDrop}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onKeyDown={handleKeyDown}
            tabIndex={0}
            role="button"
            aria-label="File upload dropzone. Press Enter or Space to browse files."
            onClick={() => fileInputRef.current?.click()}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept={ALLOWED_FILE_TYPES.join(",")}
              onChange={handleFileInputChange}
              className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
              aria-label="Select resume file"
            />

            <div className="space-y-4">
              {selectedFile ? (
                <CheckCircle className="h-12 w-12 mx-auto text-green-500" />
              ) : (
                <Upload className="h-12 w-12 mx-auto text-muted-foreground" />
              )}

              <div>
                <p className="text-lg font-medium">
                  {selectedFile ? "File Selected" : "Drop your resume here"}
                </p>
                <p className="text-sm text-muted-foreground mt-1">
                  {selectedFile
                    ? `${selectedFile.name} (${formatFileSize(selectedFile.size)})`
                    : `or click to browse • ${ALLOWED_FILE_TYPES.join(", ")} • Max ${formatFileSize(MAX_FILE_SIZE)}`
                  }
                </p>
              </div>
            </div>
          </div>

          {/* File Information Panel */}
          {selectedFile && (
            <Card className="bg-muted/50">
              <CardContent className="pt-4">
                <div className="flex items-start gap-3">
                  <FileText className="h-5 w-5 mt-0.5 text-muted-foreground" />
                  <div className="flex-1 space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="font-medium">File Information</span>
                      <span className="text-sm text-muted-foreground">Ready to upload</span>
                    </div>
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div>
                        <span className="text-muted-foreground">Name:</span>
                        <p className="font-mono break-all">{selectedFile.name}</p>
                      </div>
                      <div>
                        <span className="text-muted-foreground">Size:</span>
                        <p>{formatFileSize(selectedFile.size)}</p>
                      </div>
                      <div className="col-span-2">
                        <span className="text-muted-foreground">Hash:</span>
                        <p className="font-mono text-xs break-all mt-1">
                          {fileHash || "Calculating..."}
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Error Display */}
          {uploadState.error && (
            <Card className="border-destructive bg-destructive/5">
              <CardContent className="pt-4">
                <div className="flex items-start gap-3">
                  <AlertCircle className="h-5 w-5 mt-0.5 text-destructive" />
                  <div>
                    <p className="font-medium text-destructive">Upload Error</p>
                    <p className="text-sm text-destructive/80 mt-1">{uploadState.error}</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Action Buttons */}
          <div className="flex gap-3 pt-4">
            <Button
              onClick={handleSubmit}
              disabled={!selectedFile || uploadState.isUploading}
              className="flex-1"
              size="lg"
            >
              {uploadState.isUploading ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Uploading...
                </>
              ) : (
                <>
                  <Upload className="h-4 w-4 mr-2" />
                  Upload Resume
                </>
              )}
            </Button>

            {selectedFile && (
              <Button
                onClick={resetForm}
                variant="outline"
                disabled={uploadState.isUploading}
                size="lg"
              >
                Clear
              </Button>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}