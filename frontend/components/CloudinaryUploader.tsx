'use client'

import { useState, useRef } from 'react'
import { Upload, CheckCircle2, XCircle, Loader2, Image as ImageIcon } from 'lucide-react'
import { Button } from '@/components/ui'
import { api } from '@/lib/api'
import type { AssetRegisterRequest } from '@/types'

interface CloudinaryUploaderProps {
  analysisId: number
  creativeId: string
  onSuccess: (assetData: any) => void
  onError: (error: string) => void
  disabled?: boolean
}

export default function CloudinaryUploader({
  analysisId,
  creativeId,
  onSuccess,
  onError,
  disabled = false
}: CloudinaryUploaderProps) {
  const [uploading, setUploading] = useState(false)
  const [preview, setPreview] = useState<string | null>(null)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    // Validate file type
    if (!file.type.startsWith('image/')) {
      onError('Please select a valid image file')
      return
    }

    // Validate file size (max 10MB)
    const maxSize = 10 * 1024 * 1024
    if (file.size > maxSize) {
      onError('Image size must be less than 10MB')
      return
    }

    setSelectedFile(file)
    
    // Create preview
    const reader = new FileReader()
    reader.onloadend = () => {
      setPreview(reader.result as string)
    }
    reader.readAsDataURL(file)
  }

  const handleUpload = async () => {
    if (!selectedFile) return

    setUploading(true)

    try {
      // Step 1: Get upload signature from backend
      // Pass public_id so it's included in the signature
      console.log('Requesting signature for:', {
        folder: `creativepulse/${analysisId}`,
        publicId: creativeId
      })
      
      const signatureData = await api.getCloudinarySignature(
        `creativepulse/${analysisId}`,
        creativeId
      )
      
      console.log('Received signature data:', {
        ...signatureData,
        signature: signatureData.signature.substring(0, 10) + '...' // Don't log full signature
      })

      // Step 2: Upload directly to Cloudinary
      // Send ONLY the parameters that were signed
      const formData = new FormData()
      formData.append('file', selectedFile)
      formData.append('timestamp', signatureData.timestamp)
      formData.append('folder', signatureData.folder)
      if (signatureData.public_id) {
        formData.append('public_id', signatureData.public_id)
      }
      formData.append('signature', signatureData.signature)
      formData.append('api_key', signatureData.api_key)
      
      console.log('Uploading to Cloudinary with params:', {
        timestamp: signatureData.timestamp,
        folder: signatureData.folder,
        public_id: signatureData.public_id,
        api_key: signatureData.api_key,
        cloud_name: signatureData.cloud_name
      })

      const cloudinaryResponse = await fetch(
        `https://api.cloudinary.com/v1_1/${signatureData.cloud_name}/image/upload`,
        {
          method: 'POST',
          body: formData
        }
      )

      if (!cloudinaryResponse.ok) {
        const errorData = await cloudinaryResponse.json().catch(() => ({}))
        console.error('Cloudinary error details:', {
          status: cloudinaryResponse.status,
          statusText: cloudinaryResponse.statusText,
          error: errorData,
          sentParams: {
            folder: signatureData.folder,
            public_id: signatureData.public_id,
            timestamp: signatureData.timestamp,
            api_key: signatureData.api_key,
            cloud_name: signatureData.cloud_name
          }
        })
        throw new Error(`Cloudinary upload failed: ${errorData.error?.message || cloudinaryResponse.statusText}`)
      }

      const cloudinaryData = await cloudinaryResponse.json()
      console.log('Cloudinary upload successful:', cloudinaryData.public_id)

      // Step 3: Register asset in backend database
      const assetData: AssetRegisterRequest = {
        creative_id: creativeId,
        filename: selectedFile.name,
        cloudinary_public_id: cloudinaryData.public_id,
        cloudinary_url: cloudinaryData.url,
        secure_url: cloudinaryData.secure_url,
        width: cloudinaryData.width,
        height: cloudinaryData.height,
        format: cloudinaryData.format,
        bytes: cloudinaryData.bytes,
        source: 'cloudinary' as const
      }

      await api.registerAsset(analysisId, assetData)

      onSuccess(assetData)
    } catch (err) {
      console.error('Upload error:', err)
      onError(err instanceof Error ? err.message : 'Upload failed')
    } finally {
      setUploading(false)
    }
  }

  const handleClear = () => {
    setSelectedFile(null)
    setPreview(null)
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }

  return (
    <div className="space-y-3">
      <input
        ref={fileInputRef}
        type="file"
        accept="image/*"
        onChange={handleFileSelect}
        disabled={disabled || uploading}
        className="hidden"
      />

      {preview ? (
        <div className="relative">
          <div className="aspect-video bg-surface rounded-lg overflow-hidden border border-border">
            <img
              src={preview}
              alt={`Preview for ${creativeId}`}
              className="w-full h-full object-contain"
            />
          </div>
          {!uploading && (
            <button
              onClick={handleClear}
              className="absolute top-2 right-2 p-1 bg-background/80 backdrop-blur-sm rounded-full hover:bg-danger-600/20 transition-colors"
              aria-label="Remove image"
            >
              <XCircle className="w-4 h-4 text-text-tertiary hover:text-danger-400" />
            </button>
          )}
        </div>
      ) : (
        <button
          onClick={() => fileInputRef.current?.click()}
          disabled={disabled || uploading}
          className="w-full aspect-video bg-surface border-2 border-dashed border-border hover:border-primary-500 rounded-lg flex flex-col items-center justify-center cursor-pointer transition-all hover:bg-surface-elevated disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <ImageIcon className="w-8 h-8 text-text-tertiary mb-2" />
          <span className="text-sm text-text-secondary">Click to select image</span>
          <span className="text-xs text-text-tertiary mt-1">PNG, JPG, GIF (max 10MB)</span>
        </button>
      )}

      {selectedFile && !uploading && (
        <Button
          onClick={handleUpload}
          disabled={disabled}
          fullWidth
          size="sm"
        >
          <Upload className="w-4 h-4 mr-2" />
          Upload to Cloudinary
        </Button>
      )}

      {uploading && (
        <div className="flex items-center justify-center space-x-2 py-2 text-sm text-primary-400">
          <Loader2 className="w-4 h-4 animate-spin" />
          <span>Uploading...</span>
        </div>
      )}
    </div>
  )
}
