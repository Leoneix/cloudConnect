export interface ErrorDetail {
  code: string;
  message: string;
  details?: any;
}

export interface ApiError {
  error: ErrorDetail;
}

export interface MessageResponse {
  message: string;
}
