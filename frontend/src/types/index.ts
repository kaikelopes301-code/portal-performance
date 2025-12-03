// Types centralizados para o frontend

// === Jobs ===
export type JobStatus = 'pending' | 'processing' | 'completed' | 'failed'

export interface Job {
    id: string
    filename: string
    status: JobStatus
    region?: string | null
    month_ref?: string | null
    created_at: string
    completed_at?: string
    updated_at?: string
    error_message?: string
    file_url?: string
    result_summary?: {
        row_count: number
        unit_count: number
        sum_valor_mensal_final: number
    }
}

export interface JobListResponse {
    jobs: Job[]
    total: number
}

// === Config ===
export interface CopyTexts {
    greeting?: string
    intro?: string
    observation?: string
    cta_label?: string
    footer_signature?: string
    subject_template?: string
}

export interface SenderConfig {
    name: string
    email: string
}

export interface DefaultsConfig {
    visible_columns: string[]
    copy_texts: CopyTexts
    month_reference: string
}

export interface RegionConfig {
    copy_texts?: CopyTexts
    visible_columns?: string[]
    month_reference?: string
}

export interface UnitConfig {
    copy_texts?: CopyTexts
    visible_columns?: string[]
    month_reference?: string
    recipients?: string[]
}

export interface AppConfig {
    defaults: DefaultsConfig
    regions: Record<string, RegionConfig>
    units: Record<string, UnitConfig>
}

// === Templates ===
export interface Template {
    id: string
    name: string
    description?: string
    filename: string
    subject_template: string
    is_active: boolean
    created_at: string
    updated_at?: string
}

export interface TemplateListResponse {
    templates: Template[]
    count: number
}

export interface TemplatePreview {
    html: string
    subject: string
}

// === Schedules ===
export type ScheduleFrequency = 'daily' | 'weekly' | 'monthly'
export type ScheduleStatus = 'active' | 'paused' | 'completed'

export interface Schedule {
    id: string
    name: string
    description?: string
    region: string
    units: string[]
    frequency: ScheduleFrequency
    day_of_month?: number
    day_of_week?: number
    time: string
    auto_send_email: boolean
    template_id?: string
    status: ScheduleStatus
    created_at: string
    updated_at?: string
    last_run?: string
    next_run?: string
    run_count: number
}

export interface ScheduleListResponse {
    schedules: Schedule[]
    count: number
}

export interface ScheduleCreateRequest {
    name: string
    description?: string
    region: string
    units: string[]
    frequency: ScheduleFrequency
    day_of_month?: number
    day_of_week?: number
    time: string
    auto_send_email?: boolean
    template_id?: string
}

// === API Responses ===
export interface ApiError {
    detail: string | { msg: string; type: string }[]
}

export interface HealthResponse {
    status: string
    version: string
}

// === Email Logs ===
export interface EmailLog {
    id: number
    job_id?: number
    unit_name: string
    region?: string
    month_ref: string
    recipient_list?: string
    subject: string
    status: 'sent' | 'failed' | 'queued' | 'dry_run'
    provider?: string
    is_dry_run: boolean
    total_value?: number
    row_count?: number
    sent_at?: string
    error_message?: string
}

export interface LogStats {
    total: number
    sent: number
    failed: number
    dry_runs: number
    real_sends: number
    recent_7_days: number
    unique_units: number
}

export interface LogListResponse {
    items: EmailLog[]
    total: number
    skip: number
    limit: number
}
