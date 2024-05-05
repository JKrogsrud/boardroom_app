const removeButtons = document.getElementsByClassName("remove");
const viewButtons = document.getElementsByClassName("view");

console.log("Adding Listeners to remove buttons")
for (buttonNum in Array.from(removeButtons)) {
    const button = removeButtons[buttonNum];
    const parentElement = button.parentElement;
    const parentId = parentElement.id;
    button.addEventListener("click", () => removeEntry(parentId));
}

console.log("Adding Listeners to view buttons")

for (buttonNum in Array.from(viewButtons)) {
    const button = viewButtons[buttonNum];
    const parentElement = button.parentElement;
    const parentId = parentElement.id;
    console.log(parentId);
    button.addEventListener("click", () => viewItem(parentId));
}

function removeEntry(id) {
    console.log("Removing Entry");
    const divToRemove = document.getElementById(id);
    divToRemove.remove();
}

// Move to library
function viewItem(id) {
    console.log("Viewing Item");

    // Redirect to boardgame view page
    location.replace("/library/add/" + id);
}