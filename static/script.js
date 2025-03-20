async function uploadFiles() {
    const input = document.getElementById("fileInput");
    const files = input.files;
    if (files.length === 0) {
        alert("Select the PDF form");
        return;
    }

    const formData = new FormData();
    for (let file of files) {
        formData.append("files", file);
    }

    try {
        const response = await fetch("/api/v1/pdf-forms-check/simple-check-pdf-forms", {
            method: "POST",
            body: formData
        });

        if (!response.ok) {
            throw new Error("File loading error");
        }

        const data = await response.json();
        displayResults(data);
    } catch (error) {
        alert("Error: " + error.message);
    }
}

function displayResults(files) {
    const resultsDiv = document.getElementById("results");
    resultsDiv.innerHTML = "";

    files.forEach(file => {
        const fileInfo = document.createElement("p");
        fileInfo.innerHTML = `<strong>${file.filename}</strong> - <a href="${file.url}" target="_blank">Download</a>`;
        resultsDiv.appendChild(fileInfo);
    });
}
