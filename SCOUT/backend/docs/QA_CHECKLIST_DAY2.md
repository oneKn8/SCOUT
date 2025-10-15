# Day 2 QA Checklist - Upload Functionality

## Manual Testing Checklist

### Backend API Testing

#### Upload Endpoint (`POST /api/uploads/resume`)

**File Type Validation:**
- [ ] Upload `.pdf` file → Should succeed
- [ ] Upload `.docx` file → Should succeed
- [ ] Upload `.txt` file → Should fail with 400 error
- [ ] Upload `.jpg` file → Should fail with 400 error
- [ ] Upload file without extension → Should fail with 400 error

**File Size Validation:**
- [ ] Upload 1MB file → Should succeed
- [ ] Upload 9MB file → Should succeed
- [ ] Upload 11MB file → Should fail with 413 error
- [ ] Upload 0-byte file → Should fail with 400 error

**File Storage:**
- [ ] Verify file stored in `data/original/{YYYY}/{MM}/{run_id}/filename.ext`
- [ ] Verify directory structure created automatically
- [ ] Verify file content matches uploaded file (checksum)
- [ ] Verify multiple uploads create separate run_id directories

**Response Validation:**
- [ ] Response contains `resume_id` (UUID format)
- [ ] Response contains `run_id` (UUID format)
- [ ] Response contains `file_hash` (64-char SHA-256)
- [ ] Response contains `stored_path` (redacted format)
- [ ] Response contains `upload_timestamp` (ISO format)
- [ ] Response status is `"uploaded"`

**Error Handling:**
- [ ] Malformed requests return proper error messages
- [ ] Large files return descriptive error with size information
- [ ] Unsupported files return list of allowed types
- [ ] Network errors handled gracefully

#### Health Check Endpoints

- [ ] `GET /health` returns `{"status": "healthy"}`
- [ ] `GET /api/uploads/health` returns upload service info
- [ ] Health checks include max file size and allowed types

#### Logging Verification

- [ ] All requests logged with request_id
- [ ] Upload attempts logged with run_id and metadata
- [ ] PII redaction working (no emails/phones in logs)
- [ ] Error conditions logged with proper context
- [ ] File operations logged with redacted paths

### Frontend Interface Testing

#### File Selection

**Drag and Drop:**
- [ ] Drag valid file over dropzone → Visual feedback (blue border)
- [ ] Drop valid file → File selected, info panel appears
- [ ] Drag invalid file → Still accepts, but shows validation error
- [ ] Drag multiple files → Error message about single file limit

**Click to Browse:**
- [ ] Click dropzone → File dialog opens
- [ ] Select valid file → File info panel appears
- [ ] Cancel file dialog → No changes to UI
- [ ] File dialog filters to PDF/DOCX only

**File Information Panel:**
- [ ] Shows correct filename
- [ ] Shows formatted file size
- [ ] Shows SHA-256 hash (after calculation)
- [ ] Hash calculation works for various file sizes

#### Accessibility

**Keyboard Navigation:**
- [ ] Tab to dropzone → Focus visible with ring
- [ ] Enter/Space on dropzone → File dialog opens
- [ ] Tab to Upload button → Focus visible
- [ ] Enter/Space on Upload button → Starts upload
- [ ] Tab to Clear button → Focus visible when file selected

**Screen Reader:**
- [ ] Dropzone has proper ARIA label
- [ ] File input has descriptive label
- [ ] Upload status announced during upload
- [ ] Error messages announced when they appear
- [ ] Success message announced on completion

#### Upload Process

- [ ] Upload button disabled when no file selected
- [ ] Upload button shows loading state during upload
- [ ] Progress indication during upload (spinner)
- [ ] Clear button available when file selected
- [ ] Clear button removes file and resets form

#### Error Handling

- [ ] File type errors show in toast and error panel
- [ ] File size errors show human-readable sizes
- [ ] Network errors show user-friendly messages
- [ ] API errors display backend error messages
- [ ] Multiple errors handled gracefully

#### Upload Result View

**Trace Information Display:**
- [ ] Resume ID displayed with copy button
- [ ] Run ID displayed with copy button
- [ ] File hash displayed with copy button
- [ ] Storage path displayed (redacted) with copy button
- [ ] Upload timestamp formatted properly

**Copy Functionality:**
- [ ] Copy buttons work for all trace fields
- [ ] Toast confirms successful copy
- [ ] Error handling if clipboard API unavailable

**Navigation:**
- [ ] "Upload Another File" button resets to upload form
- [ ] "View Parsed Profile" button disabled (placeholder)
- [ ] Help text explains next steps

### Integration Testing

#### End-to-End Workflows

**Successful Upload:**
1. [ ] Select valid file → Info panel appears
2. [ ] Click upload → Loading state shown
3. [ ] Upload completes → Success toast appears
4. [ ] Result view shows → All trace info visible
5. [ ] Copy buttons work → Toast confirmations
6. [ ] Start over → Returns to upload form

**Error Recovery:**
1. [ ] Select invalid file → Error shown immediately
2. [ ] Clear and select valid file → Error clears
3. [ ] Network error during upload → Error message, can retry
4. [ ] Backend error → User-friendly message shown

#### Cross-Browser Testing

- [ ] Chrome: All functionality works
- [ ] Firefox: All functionality works
- [ ] Safari: All functionality works
- [ ] Edge: All functionality works

#### Responsive Design

- [ ] Mobile (375px): Layout adapts properly
- [ ] Tablet (768px): All elements accessible
- [ ] Desktop (1024px+): Optimal layout
- [ ] File info panel readable on small screens

### Performance Testing

- [ ] Small files (< 1MB) upload quickly
- [ ] Large files (5-10MB) upload with good UX
- [ ] Hash calculation doesn't block UI
- [ ] Multiple rapid uploads handled properly

### Security Testing

- [ ] File type validation cannot be bypassed
- [ ] File size limits enforced server-side
- [ ] No sensitive data in client-side logs
- [ ] CORS properly configured
- [ ] No XSS vulnerabilities in file names

## Automated Test Coverage

### Backend Tests Required
- [ ] File validation unit tests
- [ ] Storage service tests
- [ ] Upload endpoint integration tests
- [ ] Error handling tests
- [ ] Logging tests

### Frontend Tests Required
- [ ] File validation logic tests
- [ ] Upload form component tests
- [ ] API client tests
- [ ] Accessibility tests
- [ ] Toast notification tests

## Known Issues / Limitations

1. **Database Persistence**: Currently only file storage, no database records
2. **Authentication**: No authentication implemented (local-only)
3. **File Processing**: Files stored but not parsed/processed
4. **Cleanup**: No automatic cleanup of old uploads
5. **Concurrent Uploads**: Single file uploads only

## Sign-off

- [ ] **Frontend Developer**: All UI functionality working
- [ ] **Backend Developer**: All API endpoints working
- [ ] **QA Tester**: Manual testing completed
- [ ] **Accessibility Expert**: WCAG compliance verified
- [ ] **Security Review**: No critical vulnerabilities found

**Date:** ___________
**Tested by:** ___________
**Version:** Day 2 Implementation