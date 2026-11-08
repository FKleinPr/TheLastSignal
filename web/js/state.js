const GAME_ID_STORAGE_KEY = "last-signal-game";

export function getStoredGameId() {
    return localStorage.getItem(GAME_ID_STORAGE_KEY);
}

export function setStoredGameId(gameId) {
    localStorage.setItem(GAME_ID_STORAGE_KEY, gameId);
}

export function clearStoredGameId() {
    localStorage.removeItem(GAME_ID_STORAGE_KEY);
}

export function resumeGame() {
    const storedId = getStoredGameId();
    if (!storedId) {
        return null;
    }
    return storedId;
}

export function startNewGame() {
    clearStoredGameId();
}
