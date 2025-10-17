/**
 * 영상 URL을 토큰과 함께 fetch하여 Blob URL로 변환하는 유틸리티
 */
import httpClient from '../services/httpClient';

export const fetchVideoWithAuth = async (videoUrl) => {
  try {
    const token = localStorage.getItem('access_token');
    
    if (!token) {
      throw new Error('No authentication token found');
    }

    // Fetch video as blob with Authorization header
    const response = await fetch(videoUrl, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    // Convert to blob
    const blob = await response.blob();
    
    // Create blob URL
    const blobUrl = URL.createObjectURL(blob);
    
    return {
      success: true,
      blobUrl,
      blob
    };
    
  } catch (error) {
    console.error('Failed to fetch video with auth:', error);
    return {
      success: false,
      error: error.message
    };
  }
};

export const revokeVideoBlobUrl = (blobUrl) => {
  if (blobUrl && blobUrl.startsWith('blob:')) {
    URL.revokeObjectURL(blobUrl);
  }
};
