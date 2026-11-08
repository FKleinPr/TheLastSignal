/**
 * API client for The Last Signal game server.
 * Handles all HTTP requests to the game server.
 */

export function makeRequest(endpoint, data = null, method = "GET") {
    const url = endpoint.startsWith("http") ? endpoint : endpoint;
    const options = {
        method,
        headers: { "Content-Type": "application/json" }
    };
    
    if (data && method === "POST") {
        options.body = JSON.stringify(data);
    }
    
    return fetch(url, options).then(r => {
        if (r.status === 200 || r.status === 201) {
            return r.json();
        }
        throw new Error(`HTTP ${r.status}: ${r.statusText}`);
    });
}

export function makeRequestRaw(endpoint, data = null, method = "GET") {
    const url = endpoint.startsWith("http") ? endpoint : endpoint;
    const options = {
        method,
        headers: { "Content-Type": "application/json" }
    };
    
    if (data && method === "POST") {
        options.body = JSON.stringify(data);
    }
    
    return fetch(url, options);
}

export function newGame() {
    return makeRequest("/api/games", {}, "POST");
}

export function getGameState(gameId) {
    return makeRequest(`/api/games/${gameId}`);
}

export function sendCommand(gameId, text) {
    return makeRequest(`/api/games/${gameId}/commands`, { text }, "POST");
}

export function getPictures() {
    return makeRequest("/api/pictures");
}

export function resetTest() {
    return makeRequest("/api/test/reset", null, "POST");
}

export function scriptLlm(responses) {
    return makeRequest("/api/test/llm-script", { responses }, "POST");
}

export function setPictures(pictures) {
    return makeRequest("/api/test/pictures", { pictures }, "POST");
}

export function getChapterJson(chapter = "act1") {
    return makeRequest(`/web/chapters/${chapter}/chapter.json`);
}

export function getChaptersIndex() {
    return makeRequest("/web/chapters/index.json");
}

export function getPicturePng(name) {
    return makeRequestRaw(`/api/pictures/${name}/png`);
}

export function newGameRaw() {
    return makeRequestRaw("/api/games", {}, "POST");
}
