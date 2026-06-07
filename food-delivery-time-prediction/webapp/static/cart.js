// This array will hold all the items added to the cart
let shoppingCart = [];

// Wait for the HTML to fully load before looking for "Add to Cart" buttons
document.addEventListener("DOMContentLoaded", function() {
    // 1. Listen for clicks on ALL "Add to Cart" buttons
    document.querySelectorAll('.btn-cart').forEach(button => {
        button.addEventListener('click', function(event) {
            event.preventDefault(); // Stop the page from refreshing

            // Find the specific product box we just clicked inside
            const productBox = this.closest('.product-item');

            // Extract the Name, Price, and Quantity
            const productName = productBox.querySelector('h3').innerText;
            const priceText = productBox.querySelector('.fw-semibold').innerText;
            
            // Remove the Rupee sign and convert to a decimal number
            const productPrice = parseFloat(priceText.replace('₹', '').trim()); 
            const productQuantity = parseInt(productBox.querySelector('.quantity').value);

            // Send this data to our cart
            addToCart(productName, productPrice, productQuantity);
        });
    });
}); 

// ==========================================
// 2. CHECKOUT LOGIC 
// ==========================================
function processCheckout() {
    if (shoppingCart.length === 0) {
        alert("Your cart is empty! Add some items first.");
        return;
    }

    var addressModal = new bootstrap.Modal(document.getElementById('addressModal'));
    addressModal.show();

    fetch('/get_addresses')
    .then(res => res.json())
    .then(data => {
        const container = document.getElementById('address-list-container');
        container.innerHTML = ''; 

        if (data.length === 0) {
            container.innerHTML = `<div class="alert alert-warning">No addresses found in your profile.</div>`;
            return;
        }

        data.forEach((addr, index) => {
            let isChecked = index === 0 ? 'checked' : ''; 
            container.innerHTML += `
                <div class="form-check border rounded p-3 mb-2 bg-light shadow-sm">
                    <input class="form-check-input ms-1 me-2" type="radio" name="selectedAddress" id="addr_${addr.id}" value="${addr.id}" ${isChecked}>
                    <label class="form-check-label w-100" style="cursor: pointer;" for="addr_${addr.id}">
                        <strong class="text-success">Delivery Address ${index + 1}</strong><br>
                        <span class="text-dark small">${addr.address_text}</span>
                    </label>
                </div>
            `;
        });
    });
}

// 2.5 Submit the final order after selecting an address
function submitFinalOrder() {
    const selectedRadio = document.querySelector('input[name="selectedAddress"]:checked');
    if (!selectedRadio) {
        alert("Please select a delivery address.");
        return;
    }

    const addressId = selectedRadio.value;
    let total = shoppingCart.reduce((sum, item) => sum + (item.price * item.qty), 0);

    fetch('/checkout', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ cart: shoppingCart, total: total, address_id: addressId })
    })
    .then(response => response.json())
    .then(data => {
        alert(data.message); 
        bootstrap.Modal.getInstance(document.getElementById('addressModal')).hide();
        shoppingCart = [];   
        renderCart();        
    });
}

// 3. Function to add items to the cart array
function addToCart(name, price, qty) {
    const existingItem = shoppingCart.find(item => item.name === name);
    
    if (existingItem) {
        existingItem.qty += qty;
    } else {
        shoppingCart.push({ name: name, price: price, qty: qty });
    }

    renderCart();

    var cartPanel = bootstrap.Offcanvas.getOrCreateInstance(document.getElementById('offcanvasCart'));
    cartPanel.show();
}

// 4. Function to remove an item from the cart
function removeFromCart(name) {
    shoppingCart = shoppingCart.filter(item => item.name !== name);
    renderCart();
}

// 5. Function to update the HTML panel (CHANGED $ TO ₹)
function renderCart() {
    const listContainer = document.getElementById('cart-item-list');
    const countBadge = document.getElementById('cart-item-count');
    
    listContainer.innerHTML = ''; 
    let grandTotal = 0;
    let totalItems = 0;

    if (shoppingCart.length === 0) {
        listContainer.innerHTML = `<li class="list-group-item d-flex justify-content-center lh-sm text-muted">Your cart is empty.</li>`;
    } else {
        shoppingCart.forEach(item => {
            const itemTotal = item.price * item.qty;
            grandTotal += itemTotal;
            totalItems += item.qty;

            listContainer.innerHTML += `
                <li class="list-group-item d-flex justify-content-between lh-sm">
                    <div>
                        <h6 class="my-0">${item.name}</h6>
                        <small class="text-body-secondary">Qty: ${item.qty} x ₹${item.price.toFixed(2)}</small>
                    </div>
                    <div class="text-end">
                        <span class="text-body-secondary d-block fw-bold">₹${itemTotal.toFixed(2)}</span>
                        <button class="btn btn-sm btn-danger mt-1 py-0 px-2" onclick="removeFromCart('${item.name}')" title="Remove item">&times;</button>
                    </div>
                </li>
            `;
        });
    }

    listContainer.innerHTML += `
        <li class="list-group-item d-flex justify-content-between bg-light">
            <span class="fw-bold">Total (INR)</span>
            <strong class="text-success">₹${grandTotal.toFixed(2)}</strong>
        </li>
    `;

    countBadge.innerText = totalItems;
}

// ==========================================
// LIVE ORDER TRACKING
// ==========================================
let trackingInterval = null; // Variable to store the timer

function fetchTrackingData() {
    const trackerBody = document.getElementById('tracker-body');
    
    // Only show "Loading" on the very first click
    if (!trackingInterval) {
        trackerBody.innerHTML = '<div class="text-center text-muted py-4"><span class="spinner-border spinner-border-sm me-2"></span>Loading order details...</div>';
    }

    const performFetch = () => {
        fetch('/track_order')
            .then(response => response.json())
            .then(data => {
                if (data.message) {
                    trackerBody.innerHTML = `<div class="text-center text-muted py-4"><h5>🛒 No active orders</h5><p>Place an order to start tracking!</p></div>`;
                    stopLiveTracking();
                    return;
                }

                // Calculate the Rounded UP time from your CatBoost model
                let timeText = data.eta ? `${data.eta} Minutes` : "Calculating...";
                
                let html = `
                    <h5 class="fw-bold text-dark mb-1">Order #100${data.id}</h5>
                    <p class="text-muted small mb-3">Items: ${data.items}</p>
                    <div class="alert alert-warning text-center fw-bold fs-5 shadow-sm">
                        Status: ${data.status}
                    </div>
                `;

                if (data.status === "Out for Delivery") {
                    html += `
                    <div class="alert alert-info text-center py-2 shadow-sm border-info">
                        <strong class="text-primary">⏳ Estimated Arrival:</strong> 
                        <span class="fs-5 fw-bold text-dark">${timeText}</span>
                    </div>`;
                }

                if (data.deliverer) {
                    html += `
                    <div class="card mt-4 border-warning shadow-sm">
                        <div class="card-header bg-warning-subtle text-dark fw-bold" style="background-color: #F8DA76;">
                            🚴 Your Deliverer
                        </div>
                        <div class="card-body">
                            <h5 class="fw-bold mb-1">${data.deliverer.name}</h5>
                            <p class="mb-1"><strong>⭐ Rating:</strong> ${data.deliverer.rating} / 5.0</p>
                            <p class="mb-1"><strong>📞 Phone:</strong> ${data.deliverer.contact_number}</p>
                            <p class="mb-1"><strong>🚙 Vehicle:</strong> ${data.deliverer.vehicle_type}</p>
                            <p class="mb-3 text-dark"><strong>🏷️ Plate No:</strong> <span class="badge bg-white text-dark border border-dark fs-6 text-uppercase">${data.deliverer.vehicle_no}</span></p>
                            
                            <hr>
                            <label class="form-label small fw-bold text-muted mb-1">Rate this delivery:</label>
                            <div class="input-group input-group-sm">
                                <select class="form-select" id="rate-dropdown">
                                    <option value="5">⭐⭐⭐⭐⭐ (5) Perfect</option>
                                    <option value="4">⭐⭐⭐⭐ (4) Good</option>
                                    <option value="3">⭐⭐⭐ (3) Okay</option>
                                    <option value="2">⭐⭐ (2) Poor</option>
                                    <option value="1">⭐ (1) Terrible</option>
                                </select>
                                <button class="btn btn-warning fw-bold border-dark" onclick="submitRating('${data.deliverer_id}')">Submit</button>
                            </div>
                        </div>
                    </div>`;
                } else {
                    html += `<p class="text-center text-muted mt-4"><span class="spinner-border spinner-border-sm me-2"></span>Searching for a nearby deliverer...</p>`;
                }

                trackerBody.innerHTML = html;

                // If delivered, stop checking for updates
                if (data.status === "Delivered") {
                    stopLiveTracking();
                }
            })
            .catch(err => {
                console.error("Tracking error:", err);
            });
    };

    // Run once immediately
    performFetch();

    // Set up the interval to run every 5 seconds if not already running
    if (!trackingInterval) {
        trackingInterval = setInterval(performFetch, 5000);
    }
}

// Function to stop the timer
function stopLiveTracking() {
    if (trackingInterval) {
        clearInterval(trackingInterval);
        trackingInterval = null;
    }
}

// Stop tracking if the user closes the modal window
document.addEventListener('DOMContentLoaded', () => {
    const modalElement = document.getElementById('trackerModal');
    if (modalElement) {
        modalElement.addEventListener('hidden.bs.modal', stopLiveTracking);
    }
});

function submitRating(delivererId) {
    const score = document.getElementById('rate-dropdown').value;
    
    fetch('/rate_deliverer', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ deliverer_id: delivererId, rating: score })
    })
    .then(res => res.json())
    .then(data => {
        alert(data.message);
    });
}