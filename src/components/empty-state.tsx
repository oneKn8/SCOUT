"use client"

import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'

interface EmptyStateProps {
  icon?: React.ReactNode
  title: string
  description: string
  actionLabel?: string
  onAction?: () => void
  className?: string
}

export function EmptyState({
  icon,
  title,
  description,
  actionLabel,
  onAction,
  className = ''
}: EmptyStateProps) {
  return (
    <Card className={`w-full ${className}`}>
      <CardContent className="flex flex-col items-center justify-center py-12 text-center">
        {icon && (
          <div className="mb-4 text-muted-foreground" aria-hidden="true">
            {icon}
          </div>
        )}
        <h3 className="mb-2 text-lg font-semibold text-foreground">{title}</h3>
        <p className="mb-6 max-w-sm text-sm text-muted-foreground">
          {description}
        </p>
        {actionLabel && onAction && (
          <Button onClick={onAction} variant="outline">
            {actionLabel}
          </Button>
        )}
      </CardContent>
    </Card>
  )
}