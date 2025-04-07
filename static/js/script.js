document.addEventListener("DOMContentLoaded", function () {
    // Default mode is QA
    const storedMode = localStorage.getItem("selectedMode") || "qa";
    const qaMode = document.getElementById("qaMode");
    const prodMode = document.getElementById("prodMode");

    // Set the correct radio button based on stored mode
    if (storedMode.toLowerCase() === "production") {
        prodMode.checked = true;
    } else {
        qaMode.checked = true;
    }

    // Set form title based on mode
    updateFormTitle(storedMode.toLowerCase());

    console.log("Loaded Mode:", storedMode); // Log mode when page loads

    // Attach event listeners to both radio buttons
    document.querySelectorAll("input[name='modeSelect']").forEach((radio) => {
        radio.addEventListener("change", toggleMode);
    });

    // Fetch PACER credentials and populate fields
    fetchCredentials(storedMode.toLowerCase());

    // Handle form submission
    document.getElementById('change-pacer-form').addEventListener('submit', function (event) {
        event.preventDefault();

        const selectedMode = document.querySelector("input[name='modeSelect']:checked").value;
        const username = document.getElementById('pacer_username').value;
        const password = document.getElementById('pacer_password').value;
        
        const data = selectedMode.toLowerCase() === "production" 
            ? { "mode": "production", "prod_username": username, "prod_password": password }
            : { "mode": "qa", "qa_username": username, "qa_password": password };

        fetch('/pacer/update-credentials', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        })
        .then(response => response.json())
        .then(data => {
            const messageType = data.message ? 'success' : 'danger';
            showToast(data.message, messageType); // Show success or error toast
        })
        .catch(error => console.error("Error updating PACER credentials:", error));
    });
});

function toggleMode() {
    const selectedMode = document.querySelector("input[name='modeSelect']:checked").value;

    // Save mode preference
    localStorage.setItem("selectedMode", selectedMode);

    console.log("Selected Mode:", selectedMode); // Log mode when toggled

    // Update form title dynamically
    updateFormTitle(selectedMode);

    // Fetch PACER credentials and populate fields
    fetchCredentials(selectedMode.toLowerCase());

    fetch('/pacer/update-credentials', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ "mode": selectedMode.toLowerCase()})
    })
    .then(response => response.json())
    .then(data => {
        showToast(`${selectedMode} mode activated`, 'success'); // Show success or error toast
    })
    .catch(error => console.error("Error updating PACER credentials:", error));
}

// Function to update form title dynamically
function updateFormTitle(mode) {
    document.getElementById("form-title").innerText = 
        mode.toLowerCase() === "production" ? "Update Production Credentials" : "Update QA Credentials";
}

// Function to fetch stored credentials
function fetchCredentials(mode) {
    fetch('/pacer/get')
    .then(response => response.json())
    .then(data => {
        console.log(data)
        document.getElementById('pacer_username').value = mode === "production" ? data.prod_username || '' : data.qa_username || '';
        document.getElementById('pacer_password').value = mode === "production" ? data.prod_password || '' : data.qa_password || '';
    })
    .catch(error => console.error("Error fetching PACER credentials:", error));
}

function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        showToast('Copied to clipboard', 'success');  // Show success toast
    }).catch(err => {
        console.error('Error copying text: ', err);
        showToast('Error copying text', 'danger');  // Show error toast
    });
}

// Function to show toast notification
function showToast(message, type) {
    const toastContainer = document.getElementById('toast-message');
    const toastText = document.getElementById('toast-text');

    toastText.innerText = message;
    toastContainer.className = `toast align-items-center text-white bg-${type} border-0`;

    const toast = new bootstrap.Toast(toastContainer);
    toast.show();
}

function loadContent(page) {
    // Hide all sections
    document.querySelectorAll('.content-section').forEach(section => {
        section.style.display = "none";
    });

    // Show selected section
    const selectedSection = document.getElementById(page);
    selectedSection.style.display = "block";
}

function logout() {
    fetch('/admin/logout', {
         method: 'POST', credentials: 'same-origin' 
        }
    )
    .then(response => response.json())
    .then(data => {
            window.location.href = '/'; 
        }
    )
    .catch(error => console.error('Error:', error));
}

function deleteCase(caseNumber) {
    // Open the modal and set the message dynamically
    const modal = new bootstrap.Modal(document.getElementById('deleteModal')); // Bootstrap modal instance
    const modalMessage = document.getElementById('modal-message');
    const confirmButton = document.getElementById('confirm-delete');
    const cancelButton = document.getElementById('cancel-delete');

    modalMessage.textContent = `Are you sure you want to delete case ${caseNumber}?`;
    modal.show();

    // Confirm delete
    confirmButton.onclick = async function () {
        try {
            const response = await fetch('/cases/delete_case', {
                method: 'DELETE',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ case_number: caseNumber }),
            });

            if (response.ok) {
                showToast("Case deleted successfully!", 'success');
                fetchCases(); // Refresh the table
            } else {
                const error = await response.json();
                showToast(`Error: ${error.error}`, 'danger');
            }

            modal.hide();
        } catch (error) {
            console.error('Error deleting case:', error);
            showToast(`Error deleting case: ${error}`, 'danger');
        }
    };

    // Cancel delete
    cancelButton.onclick = function () {
        modal.hide();
    };
}

function hideAddCaseForm() {
    const form = document.getElementById('add-case-form');
    form.case_number.value = ""; // Reset input field

    let modal = bootstrap.Modal.getInstance(document.getElementById('add-case-modal'));
    if (modal) modal.hide();
}

// Submit Add Case Form
async function addCase() {
    const form = document.getElementById('add-case-form');
    const submitButton = document.getElementById('submit-btn')
    const originalButtonText = submitButton.innerHTML;

    const formData = {
        case_number: form.case_number.value
    };

    // Show loader and disable button
    submitButton.innerHTML = 'Submitting...';
    submitButton.disabled = true;

    try {
        const response = await fetch('/cases/add_case', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(formData),
        });

        hideAddCaseForm();

        if (response.ok) {
            showToast("Case Added Successfully!", 'success');
            fetchCases(); // Refresh the table
        } else {
            const error = await response.json();
            showToast(`Error: ${error.error}`, 'danger');
        }
    } catch (error) {
        hideAddCaseForm();
        
        console.error('Error submitting form:', error);
        showToast(`Error submitting form: ${error}`, 'danger');
    } finally {
        // Restore button text and re-enable button
        submitButton.innerHTML = originalButtonText;
        submitButton.disabled = false;
    }

    form.case_number.value = ""
}

// Fetch cases and populate the table
async function fetchCases() {
    try {
        const response = await fetch('/cases/get_all_cases');
        const data = await response.json();
        const tableBody = document.getElementById('cases-table-body');

        if (response.ok) {
            tableBody.innerHTML = '';
            data.cases.forEach((caseItem, index) => {
                const row = `
                    <tr>
                        <td>${index + 1}</td> <!-- Adding index here -->
                        <td>${caseItem.case_number}</td>
                        <td>${caseItem.debtor_name}</td>
                        <td>${caseItem.court}</td>
                        <td>${caseItem.filing_date ? new Date(caseItem.filing_date).toLocaleDateString() : '-'}</td>
                        <td>${caseItem.dismissed_date ? new Date(caseItem.dismissed_date).toLocaleDateString() : '-'}</td>
                        <td>
                            <i class="bi bi-arrow-clockwise text-primary me-2" 
                                style="cursor:pointer;" 
                                onclick="refreshCase('${caseItem.case_number}')" 
                                title="Refresh"></i>
                            
                            <i class="bi bi-trash text-danger" 
                                style="cursor:pointer;" 
                                onclick="deleteCase('${caseItem.case_number}')" 
                                title="Delete"></i>
                        </td>
                    </tr>
                `;
                tableBody.innerHTML += row;
            });

        } else {
            console.error('API Response:', data);
            tableBody.innerHTML = `<tr><td colspan="5">Failed to load cases. Please try again later.</td></tr>`;
        }
    } catch (error) {
        console.error('Error fetching cases:', error);
    }
}

async function refreshCase(caseNumber) {
    const icon = document.querySelector(`i[onclick="refreshCase('${caseNumber}')"]`);

    if (!icon) return; // Prevent errors if icon is not found

    // Create a loader icon
    const loader = document.createElement("i");
    loader.className = "fas fa-spinner fa-spin"; // FontAwesome spinning loader
    loader.style.color = icon.style.color; // Maintain same color as refresh icon

    icon.replaceWith(loader); // Replace refresh icon with loader

    try {
        const formData = { case_number: caseNumber };

        const response = await fetch('/cases/add_case', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(formData),
        });

        if (response.ok) {
            showToast("Case Updated Successfully!", 'success');
            fetchCases(); // Refresh the table
        } else {
            const error = await response.json();
            showToast(`Error: ${error.error}`, 'danger');
        }
    } catch (error) {
        console.error('Error updating case:', error);
        showToast(`Error updating case: ${error}`, 'danger');
    }
    finally {
        loader.replaceWith(icon); // Restore the refresh icon
    }
}

async function refreshAllCases() {
    const button = document.getElementById("refresh-cases-button");
    const text = document.getElementById("refresh-text");
    const spinner = document.getElementById("refresh-spinner");
    const originalText = button.innerHTML;

    text.style.visibility = "hidden"; // Keep space but hide text
    spinner.style.display = "inline-block"; // Show spinner
    
    button.disabled = true; // Disable button

    try {
        const response = await fetch('/cases/refresh_all_cases'); // Fetch cases
        if (!response.ok) throw new Error('Failed to refresh cases');

        const data = await response.json(); // Wait for JSON parsing

        showToast(`${data.message}`, 'success');

        fetchCases(); // Refresh the table
    } catch (error) {
        console.error('Error refreshing cases:', error);

        showToast("Error refreshing cases.", 'danger');
    } finally {
        text.style.visibility = "visible"; // Restore text
        spinner.style.display = "none"; // Hide spinner
        button.disabled = false;
    }
}

// Utility function for delay
function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

function showLoader(button) {
    button.disabled = true; // Disable the button
    button.innerHTML = "";
    let loader = document.createElement("span");
    loader.classList.add("button-loader");
    button.appendChild(loader);
}

function hideLoader(button) {
    button.disabled = false; // Enable the button
    let loader = button.querySelector(".button-loader");
    if (loader) loader.remove();
}

fetchCases();