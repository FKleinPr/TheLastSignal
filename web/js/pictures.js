import { getPictures } from "./api.js";

let pictureList = null;

export function getPictureList() {
    return pictureList;
}

export async function loadPictureList() {
    if (pictureList) {
        return pictureList;
    }
    
    try {
        pictureList = await getPictures();
        return pictureList;
    } catch (e) {
        return [];
    }
}

export function getPictureMeta(name) {
    if (!pictureList) {
        return null;
    }
    
    for (const p of pictureList) {
        if (p.name === name) {
            return p;
        }
    }
    return null;
}

export function getPlaceholder(name) {
    return `[ picture: ${name} ]`;
}
