# SCOUT Data Contracts

## Core Entities

### User
Core user entity for authentication and profile management.

| Field | Type | Required | Description | Notes |
|-------|------|----------|-------------|-------|
| id | UUID | Yes | Primary key | Auto-generated |
| email | String | Yes | User email address | Unique, validated |
| created_at | Timestamp | Yes | Account creation time | Auto-generated |
| updated_at | Timestamp | Yes | Last update time | Auto-updated |
| is_active | Boolean | Yes | Account status | Defaults to true |
| settings | JSONB | No | User preferences | Encrypted if contains PII |

### Resume
Resume document and metadata storage.

| Field | Type | Required | Description | Notes |
|-------|------|----------|-------------|-------|
| id | UUID | Yes | Primary key | Auto-generated |
| user_id | UUID | Yes | Foreign key to User | Indexed |
| title | String | Yes | Resume title/name | User-defined |
| content | JSONB | Yes | Structured resume data | See ProfileJSON schema |
| version | Integer | Yes | Version number | Auto-incremented |
| created_at | Timestamp | Yes | Creation time | Auto-generated |
| updated_at | Timestamp | Yes | Last update time | Auto-updated |
| is_active | Boolean | Yes | Active status | Soft delete flag |
| metadata | JSONB | No | Additional metadata | Processing info, tags |

### Artifact
File storage and processing artifacts.

| Field | Type | Required | Description | Notes |
|-------|------|----------|-------------|-------|
| id | UUID | Yes | Primary key | Auto-generated |
| user_id | UUID | Yes | Foreign key to User | Indexed |
| resume_id | UUID | No | Associated resume | Nullable for orphaned files |
| file_path | String | Yes | Relative file path | Under DATA_ROOT |
| file_name | String | Yes | Original filename | User upload name |
| file_size | Integer | Yes | File size in bytes | For storage management |
| mime_type | String | Yes | MIME type | Validated on upload |
| checksum | String | Yes | File integrity hash | SHA-256 |
| embedding | Vector | No | Vector embedding | pgvector, for similarity |
| created_at | Timestamp | Yes | Upload time | Auto-generated |
| processed_at | Timestamp | No | Processing completion | Null if unprocessed |
| status | Enum | Yes | Processing status | pending, processing, completed, failed |

## ProfileJSON Schema

High-level structure for structured resume data stored in Resume.content.

```json
{
  "personal": {
    "name": "string",
    "email": "string",
    "phone": "string?",
    "location": "string?",
    "summary": "string?"
  },
  "experience": [
    {
      "company": "string",
      "title": "string",
      "startDate": "string (ISO date)",
      "endDate": "string? (ISO date)",
      "description": "string",
      "achievements": ["string"]
    }
  ],
  "education": [
    {
      "institution": "string",
      "degree": "string",
      "field": "string?",
      "startDate": "string? (ISO date)",
      "endDate": "string? (ISO date)",
      "gpa": "number?"
    }
  ],
  "skills": {
    "technical": ["string"],
    "soft": ["string"],
    "languages": ["string"]
  },
  "certifications": [
    {
      "name": "string",
      "issuer": "string",
      "issueDate": "string? (ISO date)",
      "expiryDate": "string? (ISO date)",
      "credentialId": "string?"
    }
  ],
  "projects": [
    {
      "name": "string",
      "description": "string",
      "technologies": ["string"],
      "url": "string?",
      "startDate": "string? (ISO date)",
      "endDate": "string? (ISO date)"
    }
  ]
}
```

## Enums

### Processing Status
- `pending`: File uploaded, awaiting processing
- `processing`: Currently being processed
- `completed`: Processing completed successfully
- `failed`: Processing failed with errors

### Log Levels
- `DEBUG`: Detailed diagnostic information
- `INFO`: General operational messages
- `WARNING`: Warning conditions
- `ERROR`: Error conditions requiring attention

## Data Privacy Notes

- PII fields (email, phone, name) are automatically redacted in logs
- User.settings and Resume.content are encrypted at rest when containing PII
- All timestamps are stored in UTC
- Soft deletes used for user data retention compliance

## Validation Rules

- Email addresses validated with RFC 5322 compliance
- File uploads limited to 10MB
- Supported MIME types: PDF, DOC, DOCX, TXT
- Resume titles limited to 255 characters
- Vector embeddings must be 384-dimensional (sentence-transformers/all-MiniLM-L6-v2)

## Indexing Strategy

- `users.email` - Unique index for authentication
- `resumes.user_id` - Index for user resume queries
- `artifacts.user_id` - Index for user file queries
- `artifacts.resume_id` - Index for resume-artifact relationships
- `artifacts.embedding` - Vector index for similarity search (ivfflat)