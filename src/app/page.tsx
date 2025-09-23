"use client";

import { UploadForm } from "@/components/upload-form";

export default function HomePage() {
  return (
    <div className="container mx-auto py-8 px-4">
      <div className="max-w-2xl mx-auto">
        <header className="text-center mb-8">
          <h1 className="text-3xl font-bold tracking-tight text-foreground mb-2">
            SCOUT Resume Upload
          </h1>
          <p className="text-muted-foreground">
            Upload your resume to get started with profile management
          </p>
        </header>

        <UploadForm />
      </div>
    </div>
  );
}