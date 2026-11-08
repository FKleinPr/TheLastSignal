import { getStoredGameId, setStoredGameId, resumeGame, startNewGame } from "./state.js";
import { newGame, sendCommand, getGameState, getChaptersIndex, getChapterJson, resetTest, setPictures } from "./api.js";
import { renderStory, renderPictures, renderInventory, renderCommandsHint, renderDeadButtons, renderEnding, renderError, emitEvent } from "./render.js";
import { getPictureList, getPictureMeta, getPlaceholder } from "./pictures.js";

const storyContainer = document.getElementById("story");
const inputField = document.getElementById("command");
const sendBtn = document.getElementById("send");
const newGameBtn = document.getElementById("new-game");
const inventoryDiv = document.getElementById("inventory");
const commandsHintDiv = document.getElementById("commands-hints");

let gameId = null;
let currentChapter = "act1";

async function init() {
    const storedId = resumeGame();
    
    if (storedId) {
        try {
            const state = await getGameState(storedId);
            renderStory(storyContainer, "Continuing your game.", "system");
            gameId = storedId;
            inputField.value = "";
            sendCommandInternal(gameId, "look");
        } catch (e) {
            renderError(storyContainer, "Cannot reach the game server.");
            gameId = null;
        }
    } else {
        startNewGame();
        try {
            const result = await newGame();
            gameId = result.game_id;
            setStoredGameId(gameId);
            renderStory(storyContainer, result.response.text, "system");
            renderPictures(result.response.pictures, storyContainer);
            renderInventory(result.response.inventory, inventoryDiv);
            loadChapterData();
        } catch (e) {
            renderError(storyContainer, "Cannot reach the game server.");
            gameId = null;
        }
    }
    
    setupEventListeners();
}

async function loadChapterData() {
    try {
        const index = await getChaptersIndex();
        currentChapter = index.current;
        const chapter = await getChapterJson(currentChapter);
        renderCommandsHint(commandsHintDiv, chapter.commands);
    } catch (e) {
        renderCommandsHint(commandsHintDiv, null);
    }
}

async function sendCommandInternal(gameId, text) {
    try {
        const result = await sendCommand(gameId, text);
        
        renderStory(storyContainer, text, "player");
        renderStory(storyContainer, result.text, "system");
        renderPictures(result.pictures, storyContainer);
        renderInventory(result.inventory, inventoryDiv);
        
        if (result.dead) {
            renderDeadButtons(storyContainer);
        }
        
        if (result.ending) {
            renderEnding(storyContainer, `ACT I COMPLETE`);
        }
        
        return result;
    } catch (e) {
        renderError(storyContainer, "Cannot reach the game server.");
        return null;
    }
}

function setupEventListeners() {
    sendBtn.addEventListener("click", () => {
        const text = inputField.value.trim();
        if (text && gameId) {
            sendCommandInternal(gameId, text);
            inputField.value = "";
        }
    });
    
    inputField.addEventListener("keypress", (e) => {
        if (e.key === "Enter") {
            const text = inputField.value.trim();
            if (text && gameId) {
                sendCommandInternal(gameId, text);
                inputField.value = "";
            }
        }
    });
    
    newGameBtn.addEventListener("click", async () => {
        try {
            const result = await newGame();
            gameId = result.game_id;
            setStoredGameId(gameId);
            renderStory(storyContainer, "New game started.", "system");
            renderStory(storyContainer, result.response.text, "system");
            renderPictures(result.response.pictures, storyContainer);
            renderInventory(result.response.inventory, inventoryDiv);
            inputField.value = "";
        } catch (e) {
            renderError(storyContainer, "Cannot reach the game server.");
            gameId = null;
        }
    });
    
    window.addEventListener("game-event", (e) => {
        if (e.detail.event === "continue" && gameId) {
            sendCommandInternal(gameId, "continue");
        } else if (e.detail.event === "restart" && gameId) {
            sendCommandInternal(gameId, "restart");
        }
    });
    
    window.addEventListener("game-event", (e) => {
        if (e.detail.event === "continue" && gameId) {
            sendCommandInternal(gameId, "continue");
        } else if (e.detail.event === "restart" && gameId) {
            sendCommandInternal(gameId, "restart");
        }
    });
}

init();
