/**
 * Example JavaScript/Node.js client for the OCR API Service.
 * 
 * Usage:
 *   npm install axios form-data
 *   node javascript_client.js
 */

const axios = require('axios');
const FormData = require('form-data');
const fs = require('fs');
const path = require('path');

class OCRClient {
    constructor(baseUrl, apiKey) {
        this.baseUrl = baseUrl.replace(/\/$/, '');
        this.apiKey = apiKey;
    }

    /**
     * Extract text from an image file.
     * @param {string} imagePath - Path to the image file
     * @param {Object} options - OCR options
     * @returns {Promise<Object>} OCR result
     */
    async extractText(imagePath, options = {}) {
        const { language = 'eng', preprocess = true, psm = 3, oem = 3 } = options;

        const form = new FormData();
        form.append('file', fs.createReadStream(imagePath), path.basename(imagePath));

        const response = await axios.post(
            `${this.baseUrl}/ocr/extract`,
            form,
            {
                headers: {
                    'X-API-Key': this.apiKey,
                    ...form.getHeaders()
                },
                params: { language, preprocess, psm, oem }
            }
        );

        return response.data;
    }

    /**
     * Extract text with word-level details.
     * @param {string} imagePath - Path to the image file
     * @param {string} language - Language code
     * @returns {Promise<Object>} Detailed OCR result
     */
    async extractDetailed(imagePath, language = 'eng') {
        const form = new FormData();
        form.append('file', fs.createReadStream(imagePath), path.basename(imagePath));

        const response = await axios.post(
            `${this.baseUrl}/ocr/extract/detailed`,
            form,
            {
                headers: {
                    'X-API-Key': this.apiKey,
                    ...form.getHeaders()
                },
                params: { language }
            }
        );

        return response.data;
    }

    /**
     * Process multiple images in batch.
     * @param {string[]} imagePaths - Array of image file paths
     * @param {string} language - Language code
     * @returns {Promise<Object>} Batch result
     */
    async batchExtract(imagePaths, language = 'eng') {
        const form = new FormData();

        for (const imagePath of imagePaths) {
            form.append('files', fs.createReadStream(imagePath), path.basename(imagePath));
        }

        const response = await axios.post(
            `${this.baseUrl}/ocr/batch`,
            form,
            {
                headers: {
                    'X-API-Key': this.apiKey,
                    ...form.getHeaders()
                },
                params: { language }
            }
        );

        return response.data;
    }

    /**
     * Get available OCR languages.
     * @returns {Promise<Object>} Available languages
     */
    async getLanguages() {
        const response = await axios.get(
            `${this.baseUrl}/ocr/languages`,
            {
                headers: { 'X-API-Key': this.apiKey }
            }
        );

        return response.data;
    }

    /**
     * Check API health status.
     * @returns {Promise<Object>} Health status
     */
    async healthCheck() {
        const response = await axios.get(`${this.baseUrl}/health`);
        return response.data;
    }
}

// Browser/Fetch version
class OCRClientFetch {
    constructor(baseUrl, apiKey) {
        this.baseUrl = baseUrl.replace(/\/$/, '');
        this.apiKey = apiKey;
    }

    /**
     * Extract text from a File object (browser).
     * @param {File} file - File object from input
     * @param {Object} options - OCR options
     * @returns {Promise<Object>} OCR result
     */
    async extractTextFromFile(file, options = {}) {
        const { language = 'eng', preprocess = true } = options;

        const formData = new FormData();
        formData.append('file', file);

        const params = new URLSearchParams({ language, preprocess });

        const response = await fetch(
            `${this.baseUrl}/ocr/extract?${params}`,
            {
                method: 'POST',
                headers: {
                    'X-API-Key': this.apiKey
                },
                body: formData
            }
        );

        if (!response.ok) {
            throw new Error(`OCR failed: ${response.statusText}`);
        }

        return response.json();
    }
}

// Example usage
async function main() {
    const API_URL = 'http://localhost:8000';
    const API_KEY = 'ocr_your_api_key_here';  // Replace with your actual key

    const client = new OCRClient(API_URL, API_KEY);

    try {
        // Health check
        console.log('🏥 Health Check:');
        const health = await client.healthCheck();
        console.log(`   Status: ${health.status}`);
        console.log(`   Tesseract: ${health.tesseract_version}`);

        // Example: Extract text (uncomment and update path)
        // console.log('\n📝 Extracting text...');
        // const result = await client.extractText('path/to/image.png', { language: 'eng' });
        // console.log(`   Text: ${result.text.substring(0, 100)}...`);
        // console.log(`   Confidence: ${result.confidence.toFixed(1)}%`);

        console.log('\n✅ Client ready! Update the API_KEY and test with your images.');

    } catch (error) {
        console.error('Error:', error.message);
    }
}

main();

module.exports = { OCRClient, OCRClientFetch };
