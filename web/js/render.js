/**
 * Rendering functions for The Last Signal web client.
 * Uses textContent only (no HTML setting) for XSS prevention.
 */

export function renderStory(container, message, type = "player") {
    const div = document.createElement("div");
    div.className = type === "player" ? "player-message" : "response-message";
    div.textContent = message;
    container.appendChild(div);
    container.scrollTop = container.scrollHeight;
}

export function renderPictures(pictures, container) {
    if (!pictures || pictures.length === 0) {
        return;
    }
    
    const row = document.createElement("div");
    row.className = "picture-row";
    
    for (const pic of pictures) {
        const box = document.createElement("div");
        box.className = "picture-box";
        
        if (pic.available) {
            const img = document.createElement("img");
            img.src = `/api/pictures/${pic.name}/png`;
            img.alt = pic.name;
            
            // CR-004: Set width and height for pictures (scene 640x360, character 128x128, item 64x64)
            if (pic.type === "scene") {
                img.width = 640;
                img.height = 360;
                img.style.maxWidth = "100%";
            } else if (pic.type === "character") {
                img.width = 128;
                img.height = 128;
                img.style.maxWidth = "100%";
            } else {
                img.width = 64;
                img.height = 64;
                img.style.maxWidth = "100%";
            }
            img.className = "pixelated";
            
            img.onerror = function() {
                box.textContent = `[ picture: ${pic.name} ]`;
            };
            
            box.appendChild(img);
        } else {
            box.textContent = `[ picture: ${pic.name} ]`;
        }
        
        row.appendChild(box);
    }
    
    container.appendChild(row);
}

export function renderInventory(inventory, container) {
    if (!inventory || inventory.length === 0) {
        container.textContent = "You carry nothing.";
        return;
    }
    container.textContent = "You carry: " + inventory.join(", ");
}

export function renderCommandsHint(container, chapterCommands) {
    const commands = chapterCommands || ["look", "go north", "take core", "talk to jex", 
        "give coolant-bottle to jex", "use key on door", "pick lock", "wait", "save", "load", "help"];
    container.textContent = "Commands: " + commands.join(", ");
}

export function renderDeadButtons(container) {
    const buttonsDiv = document.createElement("div");
    buttonsDiv.className = "dead-buttons";
    
    const continueBtn = document.createElement("button");
    continueBtn.textContent = "Continue";
    continueBtn.onclick = () => emitEvent("continue");
    
    const restartBtn = document.createElement("button");
    restartBtn.textContent = "Restart";
    restartBtn.onclick = () => emitEvent("restart");
    
    buttonsDiv.appendChild(continueBtn);
    buttonsDiv.appendChild(restartBtn);
    
    container.appendChild(buttonsDiv);
}

export function renderEnding(container, endingTitle) {
    const div = document.createElement("div");
    div.className = "ending-message";
    div.textContent = endingTitle;
    container.appendChild(div);
    
    const playAgainBtn = document.createElement("button");
    playAgainBtn.textContent = "Play again";
    playAgainBtn.onclick = () => emitEvent("restart");
    container.appendChild(playAgainBtn);
}

export function renderError(container, message) {
    const div = document.createElement("div");
    div.className = "error-message";
    div.textContent = message;
    container.appendChild(div);
}

export function emitEvent(event) {
    window.dispatchEvent(new CustomEvent("game-event", { detail: { event } }));
}
