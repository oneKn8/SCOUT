"use client";

import React from "react";
import { CheckCircle, Copy, FileText, RotateCcw, ExternalLink } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { useToast } from "@/hooks/use-toast";
import { formatFileSize } from "@/lib/utils";
import { UploadResponse } from "@/types/upload";

interface UploadResultProps {
  result: UploadResponse;
  onStartOver: () => void;
}

export function UploadResult({ result, onStartOver }: UploadResultProps) {
  const { toast } = useToast();

  const copyToClipboard = async (text: string, label: string) => {
    try {
      await navigator.clipboard.writeText(text);
      toast({
        title: "Copied to Clipboard",
        description: `${label} has been copied to your clipboard.`,
      });
    } catch (error) {
      toast({
        variant: "destructive",
        title: "Copy Failed",
        description: "Unable to copy to clipboard. Please select and copy manually.",
      });
    }
  };

  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleString();
  };

  return (
    <div className="w-full max-w-2xl mx-auto space-y-6">
      <Card className="border-green-500 bg-green-50 dark:bg-green-950/20">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-green-700 dark:text-green-300">
            <CheckCircle className="h-5 w-5" />
            Upload Successful
          </CardTitle>
          <CardDescription className="text-green-600 dark:text-green-400">
            Your resume has been uploaded and processed successfully.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* File Summary */}
          <div className="flex items-start gap-3 p-4 bg-background rounded-lg border">
            <FileText className="h-5 w-5 mt-0.5 text-muted-foreground" />
            <div className="flex-1">
              <h3 className="font-medium mb-2">File Summary</h3>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-muted-foreground">Filename:</span>
                  <p className="font-mono break-all">{result.file_name}</p>
                </div>
                <div>
                  <span className="text-muted-foreground">Size:</span>
                  <p>{formatFileSize(result.file_size)}</p>
                </div>
                <div>
                  <span className="text-muted-foreground">Type:</span>
                  <p>{result.mime_type}</p>
                </div>
                <div>
                  <span className="text-muted-foreground">Status:</span>
                  <p className="capitalize text-green-600 dark:text-green-400 font-medium">
                    {result.status}
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Trace Information */}
          <div className="space-y-4">
            <h3 className="font-medium">Trace Information</h3>

            <div className="grid gap-4">
              {/* Resume ID */}
              <div className="flex items-center justify-between p-3 bg-muted/50 rounded-lg">
                <div className="flex-1">
                  <label className="text-sm font-medium text-muted-foreground">Resume ID</label>
                  <p className="font-mono text-sm break-all mt-1">{result.resume_id}</p>
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => copyToClipboard(result.resume_id, "Resume ID")}
                  className="ml-2"
                >
                  <Copy className="h-3 w-3" />
                  <span className="sr-only">Copy Resume ID</span>
                </Button>
              </div>

              {/* Run ID */}
              <div className="flex items-center justify-between p-3 bg-muted/50 rounded-lg">
                <div className="flex-1">
                  <label className="text-sm font-medium text-muted-foreground">Run ID</label>
                  <p className="font-mono text-sm break-all mt-1">{result.run_id}</p>
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => copyToClipboard(result.run_id, "Run ID")}
                  className="ml-2"
                >
                  <Copy className="h-3 w-3" />
                  <span className="sr-only">Copy Run ID</span>
                </Button>
              </div>

              {/* File Hash */}
              <div className="flex items-center justify-between p-3 bg-muted/50 rounded-lg">
                <div className="flex-1">
                  <label className="text-sm font-medium text-muted-foreground">File Hash (SHA-256)</label>
                  <p className="font-mono text-xs break-all mt-1">{result.file_hash}</p>
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => copyToClipboard(result.file_hash, "File Hash")}
                  className="ml-2"
                >
                  <Copy className="h-3 w-3" />
                  <span className="sr-only">Copy File Hash</span>
                </Button>
              </div>

              {/* Storage Path */}
              <div className="flex items-center justify-between p-3 bg-muted/50 rounded-lg">
                <div className="flex-1">
                  <label className="text-sm font-medium text-muted-foreground">Storage Path</label>
                  <p className="font-mono text-sm break-all mt-1">{result.stored_path}</p>
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => copyToClipboard(result.stored_path, "Storage Path")}
                  className="ml-2"
                >
                  <Copy className="h-3 w-3" />
                  <span className="sr-only">Copy Storage Path</span>
                </Button>
              </div>

              {/* Upload Timestamp */}
              <div className="p-3 bg-muted/50 rounded-lg">
                <label className="text-sm font-medium text-muted-foreground">Upload Timestamp</label>
                <p className="text-sm mt-1">{formatTimestamp(result.upload_timestamp)}</p>
              </div>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex gap-3 pt-4">
            <Button
              variant="outline"
              onClick={onStartOver}
              className="flex-1"
              size="lg"
            >
              <RotateCcw className="h-4 w-4 mr-2" />
              Upload Another File
            </Button>

            <Button
              variant="default"
              disabled
              className="flex-1"
              size="lg"
            >
              <ExternalLink className="h-4 w-4 mr-2" />
              View Parsed Profile
              <span className="sr-only">(Coming Soon)</span>
            </Button>
          </div>

          {/* Help Text */}
          <div className="text-xs text-muted-foreground p-3 bg-muted/30 rounded-lg">
            <p className="font-medium mb-1">What happens next?</p>
            <ul className="list-disc list-inside space-y-1">
              <li>Your resume has been securely stored in the local filesystem</li>
              <li>A unique trace ID has been generated for tracking this upload</li>
              <li>You can use the Resume ID to reference this file in future operations</li>
              <li>Profile parsing and analysis features are coming soon</li>
            </ul>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}