# Day 2 Known Limitations

## Database Persistence
**Status**: Not implemented in Day 2

**Current State**:
- Files are stored in the filesystem with proper directory structure
- Upload metadata (resume_id, run_id, file_hash) is generated and returned
- No database records are created for uploads

**Next Steps**:
- Add database connection and session management
- Create database models for User, Resume, and Artifact tables
- Implement database persistence in upload endpoint
- Add database queries for retrieving upload history

## Authentication
**Status**: Intentionally omitted for local development

**Current State**:
- All endpoints are public (no authentication required)
- Suitable for local-first development environment
- CORS configured for frontend access

**Future Implementation**:
- Add authentication middleware when needed
- Implement user session management
- Add user-scoped file access controls

## File Processing
**Status**: Storage only, no content processing

**Current State**:
- Files are stored with metadata (name, size, hash, path)
- No content extraction or parsing
- No vector embeddings generated

**Planned Features**:
- PDF/DOCX content extraction
- Resume parsing and structured data extraction
- Vector embedding generation for similarity search
- Profile analysis and recommendations

## Scalability Considerations
**Current Limitations**:
- Single file uploads only
- No upload progress tracking
- No file cleanup or retention policies
- No compression or optimization

**Future Enhancements**:
- Batch upload support
- Upload progress streaming
- Automatic file cleanup based on age/size
- File compression and deduplication

## Error Recovery
**Current State**:
- Basic error handling with structured logging
- No retry mechanisms
- No partial upload recovery

**Improvements Needed**:
- Retry logic for transient failures
- Partial upload resumption
- Dead letter queue for failed uploads
- Monitoring and alerting for failures

## Performance
**Not Optimized For**:
- Large file uploads (>10MB limit in place)
- High concurrent upload volume
- Large-scale file storage

**Current Design Targets**:
- Individual user, local development
- Small to medium files (resumes, documents)
- Single-user concurrent access patterns

These limitations are intentional for the Day 2 MVP and will be addressed in future iterations based on requirements and usage patterns.