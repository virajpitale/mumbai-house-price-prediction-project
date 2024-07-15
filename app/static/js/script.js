document.addEventListener('DOMContentLoaded', () => {
    fetch('/dropdown-options/')
        .then(response => response.json())
        .then(options => {
            populateDropdown('age_encoded', options.age_options);
            populateDropdown('status_encoded', options.status_options);
            populateDropdown('type_encoded', options.type_options);
            
            setupAutocomplete('region', options.region_options);
            setupAutocomplete('locality', options.locality_options);
        })
        .catch(error => console.error('Error fetching dropdown options:', error));
});

function populateDropdown(dropdownId, options) {
    const dropdown = document.getElementById(dropdownId);
    dropdown.innerHTML = '';  // Clear existing options to prevent duplication
    options.forEach(option => {
        const optionElement = document.createElement('option');
        optionElement.text = option;
        optionElement.value = option;
        dropdown.appendChild(optionElement);
    });
}

function setupAutocomplete(inputId, options) {
    $(`#${inputId}`).autocomplete({
        source: options
    });
}

// Handle form submission and update predicted price
const predictionForm = document.getElementById('predictionForm');

predictionForm.addEventListener('submit', async (event) => {
    event.preventDefault();

    const formData = new FormData(predictionForm);

    try {
        const response = await fetch('/predict/', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            throw new Error('Network response was not ok');
        }

        const data = await response.json();
        const predictedPrice = parseFloat(data.predicted_price);

        // Update predicted price display
        const predictedPriceElement = document.getElementById('predictedPrice');
        let displayText;
        if (predictedPrice >= 100) {
            // Convert to crores if predicted price is 100 lakhs or more
            const croreValue = (predictedPrice / 100).toFixed(2);
            displayText = croreValue === '1.00' ? '1 crore' : `${croreValue} crores`;
        } else {
            // Display in lakhs for predicted price less than 100 lakhs
            displayText = predictedPrice.toFixed(2) + ' lakhs';
        }

        predictedPriceElement.textContent = displayText;

        // Show predicted price container
        const predictedPriceContainer = document.getElementById('predictedPriceContainer');
        predictedPriceContainer.style.display = 'block';
    } catch (error) {
        console.error('Error:', error);
        alert('An error occurred while predicting the price. Please try again.');
    }
});
