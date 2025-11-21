export interface BorderCircle {
  type: 'circle'
  center: { x: number; y: number }
  radius: number
  confidence?: number
}

export interface BorderEllipse {
  type: 'ellipse'
  center: { x: number; y: number }
  axes: { major: number; minor: number }
  angle: number
  confidence?: number
}

export type BorderInfo = BorderCircle | BorderEllipse

export interface DiscImage {
  image_id: number
  image_url: string
  image_path: string | null
  cropped_image_path: string | null
  border_info: BorderInfo | null
}

export interface Disc {
  disc_id: number
  owner_name: string
  owner_contact: string
  disc_model: string | null
  disc_color: string | null
  notes: string | null
  status: string
  location: string | null
  registered_date: string
  image_id: number | null
  image_url: string | null
  image_path: string | null
  border_info: BorderInfo | null
  cropped_image_path: string | null
  created_at: string | null
}

export interface UploadResult {
  disc_id: number
  border_detected: boolean
  border: BorderInfo | null
  image_url: string
  message: string
}
