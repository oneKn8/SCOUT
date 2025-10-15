"use client";

import { useState } from 'react'
import { UploadForm } from "@/components/upload-form";
import { ProfileViewer } from "@/components/profile-viewer";

export default function HomePage() {
  const [currentView, setCurrentView] = useState<'upload' | 'profile'>('upload')
  const [profileData, setProfileData] = useState<any>(null)

  const handleUploadSuccess = async (result: any) => {
    // After successful upload, trigger parsing using the stored file path
    if (result.stored_path) {
      try {
        const apiBaseUrl = process.env.NEXT_PUBLIC_API_URL || `${window.location.protocol}//${window.location.hostname}:8000`;
        const parseResponse = await fetch(`${apiBaseUrl}/api/parsing/run/file?file_path=${encodeURIComponent(result.stored_path)}`, {
          method: 'POST'
        })

        if (parseResponse.ok) {
          const parseResult = await parseResponse.json()
          if (parseResult.status === 'completed' && parseResult.result) {
            setProfileData(parseResult.result)
            setCurrentView('profile')
          }
        }
      } catch (error) {
        console.error('Failed to parse resume:', error)
      }
    }
  }

  const handleBackToUpload = () => {
    setCurrentView('upload')
    setProfileData(null)
  }

  if (currentView === 'profile' && profileData) {
    return <ProfileViewer profile={profileData} onBack={handleBackToUpload} />
  }

  return (
    <div className="container mx-auto py-8 px-4">
      <div className="max-w-2xl mx-auto">
        <header className="text-center mb-8">
          <h1 className="text-3xl font-bold tracking-tight text-foreground mb-2">
            SCOUT Resume Upload
          </h1>
          <p className="text-muted-foreground">
            Upload your resume to get started with profile management and parsing
          </p>
        </header>

        <UploadForm onUploadSuccess={handleUploadSuccess} />
      </div>
    </div>
  );
}