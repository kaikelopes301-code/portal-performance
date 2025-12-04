// Barrel export para todos os services
export { api, ApiError, getToken, setToken, clearToken } from './api'
export { jobService } from './jobService'
export type { FileWithRegion, RegionsResponse } from './jobService'
export { configService } from './configService'
export { templateService } from './templateService'
export { scheduleService } from './scheduleService'
export { emailService, generateDefaultSubject } from './emailService'
export type { HtmlFileInfo, EditableTexts, SendEmailRequest, SendEmailResponse, PreviewStats } from './emailService'
