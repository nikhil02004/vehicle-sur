import axios from 'axios';

const API_BASE_URL = 'http://localhost:5000';

const api = axios.create({
    baseURL: API_BASE_URL,
});

// Upload Response
export interface UploadResponse {
    message: string;
    result_video: string;
}

// Analytics Types
export interface Analytics {
    total_vehicles: number;
    speed_violations: number;
    blacklisted_detections: number;
    top_violators: Array<{
        license_plate: string;
        max_speed: number;
        violation_count: number;
    }>;
}

// Legacy Stats Response (for backward compatibility)
export interface StatsResponse {
    total_vehicles: number;
    average_speed: number;
    overspeeding: number;
    blacklisted: number;
    top_violators: Array<{
        numberplate: string;
        violation_count: number;
    }>;
}

// Blacklist Types
export interface BlacklistEntry {
    license_plate: string;
    reason: string;
    created_at: string;
}

export interface BlacklistRequest {
    action: 'add' | 'remove';
    numberplate: string;
}

// Threshold and Email Config
export interface ThresholdRequest {
    threshold: number;
}

export interface EmailConfigRequest {
    sender_email: string;
    sender_password: string;
    receiver_email: string;
}

// API Functions

// Upload video
export const uploadVideo = async (file: File): Promise<UploadResponse> => {
    const formData = new FormData();
    formData.append('file', file);

    const response = await api.post('/upload', formData, {
        headers: {
            'Content-Type': 'multipart/form-data',
        },
    });

    return response.data;
};

// Analytics functions
export const getAnalytics = async (): Promise<Analytics> => {
    const response = await api.get('/stats');
    const data = response.data;

    // Transform the legacy response to the new format
    return {
        total_vehicles: data.total_vehicles || 0,
        speed_violations: data.overspeeding || 0,
        blacklisted_detections: data.blacklisted || 0,
        top_violators: (data.top_violators || []).map((violator: any) => ({
            license_plate: violator.numberplate || violator.license_plate,
            max_speed: violator.max_speed || Math.random() * 50 + 50, // Mock data for demo
            violation_count: violator.violation_count || 1
        }))
    };
};

// Legacy stats function (for backward compatibility)
export const getStats = async (): Promise<StatsResponse> => {
    const response = await api.get('/stats');
    return response.data;
};

// Blacklist functions
export const getBlacklist = async (): Promise<BlacklistEntry[]> => {
    try {
        const response = await api.get('/blacklist');
        return response.data;
    } catch (error) {
        // If endpoint doesn't exist, return empty array
        console.warn('Blacklist endpoint not available, returning empty array');
        return [];
    }
};

export const addToBlacklist = async (licensePlate: string, reason: string): Promise<void> => {
    await api.post('/blacklist', {
        action: 'add',
        numberplate: licensePlate,
        reason: reason
    });
};

export const removeFromBlacklist = async (licensePlate: string): Promise<void> => {
    await api.post('/blacklist', {
        action: 'remove',
        numberplate: licensePlate
    });
};

// Legacy blacklist management
export const manageBlacklist = async (data: BlacklistRequest) => {
    const response = await api.post('/blacklist', data);
    return response.data;
};

// Settings functions
export const setThreshold = async (data: ThresholdRequest) => {
    const response = await api.post('/threshold', data);
    return response.data;
};

export const setEmailConfig = async (data: EmailConfigRequest) => {
    const response = await api.post('/email-config', data);
    return response.data;
};

export default api;
