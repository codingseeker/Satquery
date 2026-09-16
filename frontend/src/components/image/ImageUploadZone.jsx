import React, { useState, useRef, useCallback } from 'react';
import { Upload, X, Image as ImageIcon } from 'lucide-react';
import { validateFile, generateId, canPreviewInBrowser } from '../../utils/fileUtils';
import FileCard from './FileCard';

export default function ImageUploadZone({ uploadedFiles, onFilesAdded, onFileRemove, maxFiles = 4 }) {
  const [isDragging, setIsDragging] = useState(false);
  const [errors, setErrors] = useState([]);
  const fileInputRef = useRef();

  const processFiles = useCallback((rawFiles) => {
    const newErrors = [];
    const validFiles = [];

    Array.from(rawFiles).forEach(file => {
      const { valid, error } = validateFile(file);
      if (valid) {
        if (uploadedFiles.length + validFiles.length >= maxFiles) {
          newErrors.push(`Maximum ${maxFiles} files allowed.`);
          return;
        }
        validFiles.push({
          id: generateId(),
          file,
          name: file.name,
          url: canPreviewInBrowser(file) ? URL.createObjectURL(file) : null,
          status: 'ready',
          error: null,
          metadata: null,
          uploadProgress: 0,
        });
      } else {
        newErrors.push(`${file.name}: ${error}`);
      }
    });

    setErrors(newErrors);
    if (validFiles.length > 0) onFilesAdded(validFiles);
  }, [uploadedFiles, maxFiles, onFilesAdded]);

  const onDragOver = (e) => { e.preventDefault(); setIsDragging(true); };
  const onDragLeave = () => setIsDragging(false);
  const onDrop = useCallback((e) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files?.length) processFiles(e.dataTransfer.files);
  }, [processFiles]);

  const canAddMore = uploadedFiles.length < maxFiles;

  return (
    <div className="upload-zone-wrap">
      {uploadedFiles.length > 0 && (
        <div className="upload-file-list">
          {uploadedFiles.map(f => (
            <FileCard key={f.id} uploadedFile={f} onRemove={() => onFileRemove(f.id)} />
          ))}
        </div>
      )}

      {canAddMore && (
        <div
          className={`drop-zone ${isDragging ? 'drop-zone-active' : ''}`}
          onClick={() => fileInputRef.current?.click()}
          onDragOver={onDragOver}
          onDragLeave={onDragLeave}
          onDrop={onDrop}
          role="button"
          tabIndex={0}
          onKeyDown={e => e.key === 'Enter' && fileInputRef.current?.click()}
          aria-label="Upload satellite imagery"
        >
          <input
            ref={fileInputRef}
            type="file"
            hidden
            multiple
            accept=".tif,.tiff,.png,.jpg,.jpeg,image/tiff,image/png,image/jpeg"
            onChange={e => { if (e.target.files?.length) processFiles(e.target.files); e.target.value = ''; }}
          />
          <div className="drop-zone-inner">
            <div className="drop-zone-icon">
              {isDragging ? <Upload size={20} /> : <ImageIcon size={20} />}
            </div>
            <div className="drop-zone-text">
              <strong>{isDragging ? 'Drop to upload' : 'Upload satellite imagery'}</strong>
              <span>Click to browse or drag &amp; drop</span>
              <small>GeoTIFF · TIFF · PNG · JPEG</small>
            </div>
          </div>
        </div>
      )}

      {errors.length > 0 && (
        <div className="upload-errors">
          {errors.map((e, i) => <div key={i} className="upload-error-item"><X size={11} /> {e}</div>)}
          <button className="upload-errors-dismiss" onClick={() => setErrors([])}>Dismiss</button>
        </div>
      )}
    </div>
  );
}
