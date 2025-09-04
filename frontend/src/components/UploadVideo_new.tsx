import React, { useState, useRef } from 'react';
import { uploadVideo } from '../services/api';
import { Upload, Video, X, CheckCircle, AlertCircle, Play } from 'lucide-react';

const UploadVideo: React.FC = () => {
    const [file, setFile] = useState<File | null>(null);
    const [uploading, setUploading] = useState(false);
    const [result, setResult] = useState<string | null>(null);
    const [error, setError] = useState<string | null>(null);
    const fileInputRef = useRef<HTMLInputElement>(null);

    const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
        const selectedFile = event.target.files?.[0];
        if (selectedFile) {
            setFile(selectedFile);
            setError(null);
        }
    };

    const handleDrop = (event: React.DragEvent<HTMLDivElement>) => {
        event.preventDefault();
        const droppedFile = event.dataTransfer.files[0];
        if (droppedFile && droppedFile.type.startsWith('video/')) {
            setFile(droppedFile);
            setError(null);
        } else {
            setError('Please drop a valid video file');
        }
    };

    const handleDragOver = (event: React.DragEvent<HTMLDivElement>) => {
        event.preventDefault();
    };

    const handleUpload = async () => {
        if (!file) return;

        setUploading(true);
        setError(null);

        try {
            const response = await uploadVideo(file);
            setResult(response.result_video);
        } catch (err: any) {
            setError(err.response?.data?.error || 'Upload failed');
        } finally {
            setUploading(false);
        }
    };

    const resetUpload = () => {
        setFile(null);
        setResult(null);
        setError(null);
        if (fileInputRef.current) {
            fileInputRef.current.value = '';
        }
    };

    return (
        <div className="max-w-4xl mx-auto animate-fadeIn">
            <div className="bg-white rounded-xl shadow-lg glass-effect border border-gray-200 p-8 card-hover">
                <div className="text-center mb-8">
                    <h2 className="text-3xl font-bold gradient-text mb-2">🎬 Upload Video for Processing</h2>
                    <p className="text-gray-600">Upload your video to detect vehicles and analyze traffic violations</p>
                </div>

                {!result && (
                    <div className="space-y-8">
                        {/* Enhanced Drop Zone */}
                        <div
                            className={`border-2 border-dashed rounded-xl p-12 text-center transition-all duration-300 cursor-pointer card-hover ${file
                                ? 'border-green-400 bg-green-50 shadow-lg transform scale-105'
                                : 'border-gray-300 hover:border-blue-400 bg-gray-50 hover:bg-blue-50 hover:shadow-md'
                                }`}
                            onDrop={handleDrop}
                            onDragOver={handleDragOver}
                            onClick={() => fileInputRef.current?.click()}
                        >
                            <input
                                ref={fileInputRef}
                                type="file"
                                accept="video/*"
                                onChange={handleFileSelect}
                                className="hidden"
                            />

                            {file ? (
                                <div className="space-y-4 animate-fadeIn">
                                    <Video className="mx-auto h-16 w-16 text-green-500 animate-bounce" />
                                    <div>
                                        <p className="text-xl font-semibold text-green-700">{file.name}</p>
                                        <p className="text-sm text-green-600 mt-1">
                                            📁 {(file.size / (1024 * 1024)).toFixed(2)} MB
                                        </p>
                                    </div>
                                    <button
                                        onClick={(e) => {
                                            e.stopPropagation();
                                            resetUpload();
                                        }}
                                        className="inline-flex items-center px-4 py-2 bg-red-100 text-red-700 rounded-lg hover:bg-red-200 transition-all card-hover"
                                    >
                                        <X className="w-4 h-4 mr-2" />
                                        Remove
                                    </button>
                                </div>
                            ) : (
                                <div className="space-y-4 animate-fadeIn">
                                    <Upload className="mx-auto h-16 w-16 text-gray-400" />
                                    <div>
                                        <p className="text-xl font-medium text-gray-700">Drop your video here</p>
                                        <p className="text-sm text-gray-500 mt-2">
                                            or <span className="text-blue-600 font-medium">click to browse</span>
                                        </p>
                                        <p className="text-xs text-gray-400 mt-2">
                                            Supports: MP4, AVI, MOV, MKV (Max: 100MB)
                                        </p>
                                    </div>
                                </div>
                            )}
                        </div>

                        {/* Enhanced Upload Button */}
                        {file && (
                            <div className="text-center animate-fadeIn">
                                <button
                                    onClick={handleUpload}
                                    disabled={uploading}
                                    className={`inline-flex items-center px-8 py-4 rounded-xl font-semibold text-white transition-all card-hover ${uploading
                                        ? 'bg-gray-400 cursor-not-allowed'
                                        : 'bg-blue-600 hover:bg-blue-700 transform hover:scale-105 shadow-lg'
                                        }`}
                                >
                                    {uploading ? (
                                        <>
                                            <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-3"></div>
                                            Processing Video...
                                        </>
                                    ) : (
                                        <>
                                            <Play className="w-5 h-5 mr-3" />
                                            Start Processing
                                        </>
                                    )}
                                </button>
                            </div>
                        )}

                        {/* Enhanced Error Display */}
                        {error && (
                            <div className="bg-red-50 border border-red-200 rounded-xl p-4 animate-fadeIn">
                                <div className="flex items-center">
                                    <AlertCircle className="h-5 w-5 text-red-500 mr-3" />
                                    <p className="text-red-700 font-medium">{error}</p>
                                </div>
                            </div>
                        )}
                    </div>
                )}

                {/* Enhanced Result Display */}
                {result && (
                    <div className="space-y-6 animate-fadeIn">
                        <div className="text-center">
                            <CheckCircle className="mx-auto h-16 w-16 text-green-500 animate-bounce mb-4" />
                            <h3 className="text-2xl font-bold text-green-700 mb-2">✅ Processing Complete!</h3>
                            <p className="text-gray-600">Your video has been processed successfully</p>
                        </div>

                        <div className="bg-green-50 border border-green-200 rounded-xl p-6 glass-effect">
                            <h4 className="text-lg font-semibold text-green-800 mb-4 flex items-center">
                                🎥 Processed Video
                            </h4>
                            <div className="bg-black rounded-lg overflow-hidden shadow-lg">
                                <video
                                    controls
                                    className="w-full max-h-96"
                                    src={`http://localhost:5000/results/${result}`}
                                >
                                    Your browser does not support the video tag.
                                </video>
                            </div>
                            <div className="mt-4 flex space-x-4">
                                <a
                                    href={`http://localhost:5000/results/${result}`}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="inline-flex items-center px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-all card-hover shadow-lg"
                                >
                                    <Play className="w-4 h-4 mr-2" />
                                    View Full Screen
                                </a>
                                <button
                                    onClick={resetUpload}
                                    className="inline-flex items-center px-6 py-3 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-all card-hover shadow-lg"
                                >
                                    <Upload className="w-4 h-4 mr-2" />
                                    Upload Another
                                </button>
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};

export default UploadVideo;
