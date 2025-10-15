"use client"

interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg'
  message?: string
  className?: string
}

export function LoadingSpinner({ size = 'md', message, className = '' }: LoadingSpinnerProps) {
  const sizeClasses = {
    sm: 'w-4 h-4',
    md: 'w-8 h-8',
    lg: 'w-12 h-12'
  }

  return (
    <div className={`flex flex-col items-center justify-center space-y-2 ${className}`} role="status" aria-live="polite">
      <div
        className={`${sizeClasses[size]} animate-spin rounded-full border-2 border-gray-300 border-t-blue-600`}
        aria-label="Loading"
      />
      {message && (
        <p className="text-sm text-muted-foreground text-center" aria-live="polite">
          {message}
        </p>
      )}
      <span className="sr-only">Loading, please wait...</span>
    </div>
  )
}