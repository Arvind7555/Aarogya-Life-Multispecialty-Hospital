// Hospital Management System JavaScript Helpers

// Modal management
function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.remove('hidden');
        modal.classList.add('flex');
        document.body.style.overflow = 'hidden';
    }
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.add('hidden');
        modal.classList.remove('flex');
        document.body.style.overflow = 'auto';
    }
}

// Close modal when clicking backdrop
document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.modal-backdrop').forEach(modal => {
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.classList.add('hidden');
                modal.classList.remove('flex');
                document.body.style.overflow = 'auto';
            }
        });
    });
});

// Dynamic Doctor fee loading for appointment booking
function handleDoctorSelect(selectElement, feeInputId, cabinInputId) {
    const docId = selectElement.value;
    if (!docId) return;

    fetch(`/api/doctor/${docId}`)
        .then(res => res.json())
        .then(data => {
            if (feeInputId) {
                const feeEl = document.getElementById(feeInputId);
                if (feeEl) feeEl.value = data.consultation_fee;
            }
            if (cabinInputId) {
                const cabinEl = document.getElementById(cabinInputId);
                if (cabinEl) cabinEl.innerText = `Cabin: ${data.cabin_no} | Timings: ${data.available_time}`;
            }
            // Recalculate bill if in billing modal
            calculateBill();
        })
        .catch(err => console.error('Error fetching doctor data:', err));
}

// Dynamic itemized charges for billing modal
function addChargeItemRow() {
    const container = document.getElementById('charges-container');
    if (!container) return;

    const row = document.createElement('div');
    row.className = 'grid grid-cols-12 gap-2 mb-2 items-center charge-row';
    row.innerHTML = `
        <div class="col-span-7">
            <input type="text" name="item_name[]" placeholder="Item/Service/Lab Test (e.g. ECG, Blood Test)" 
                   class="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:ring-2 focus:ring-sky-500 focus:outline-none">
        </div>
        <div class="col-span-4">
            <div class="relative">
                <span class="absolute left-3 top-2 text-slate-400 text-sm">₹</span>
                <input type="number" step="0.01" min="0" name="item_cost[]" placeholder="0.00" 
                       oninput="calculateBill()"
                       class="w-full pl-7 pr-3 py-2 text-sm border border-slate-300 rounded-lg focus:ring-2 focus:ring-sky-500 focus:outline-none item-cost">
            </div>
        </div>
        <div class="col-span-1 text-center">
            <button type="button" onclick="removeChargeItemRow(this)" class="text-rose-500 hover:text-rose-700 p-1">
                <i class="fa-solid fa-trash-can"></i>
            </button>
        </div>
    `;
    container.appendChild(row);
}

function removeChargeItemRow(button) {
    const row = button.closest('.charge-row');
    if (row) {
        row.remove();
        calculateBill();
    }
}

// Live calculation for billing modal
function calculateBill() {
    const feeEl = document.getElementById('billing_consultation_fee');
    const discountEl = document.getElementById('billing_discount');
    const taxEl = document.getElementById('billing_tax');
    const paidEl = document.getElementById('billing_paid');

    const subtotalDisplay = document.getElementById('billing_subtotal_display');
    const totalDisplay = document.getElementById('billing_total_display');
    const dueDisplay = document.getElementById('billing_due_display');

    let consultationFee = feeEl ? (parseFloat(feeEl.value) || 0) : 0;
    let additionalTotal = 0;

    document.querySelectorAll('.item-cost').forEach(input => {
        additionalTotal += (parseFloat(input.value) || 0);
    });

    const subtotal = consultationFee + additionalTotal;
    const discount = discountEl ? (parseFloat(discountEl.value) || 0) : 0;
    const discounted = Math.max(0, subtotal - discount);

    const taxPercent = taxEl ? (parseFloat(taxEl.value) || 0) : 0;
    const taxAmt = (discounted * taxPercent) / 100;

    const grandTotal = Math.round((discounted + taxAmt) * 100) / 100;
    const paid = paidEl ? (parseFloat(paidEl.value) || 0) : 0;
    const balanceDue = Math.max(0, Math.round((grandTotal - paid) * 100) / 100);

    if (subtotalDisplay) subtotalDisplay.innerText = `₹${subtotal.toFixed(2)}`;
    if (totalDisplay) totalDisplay.innerText = `₹${grandTotal.toFixed(2)}`;
    if (dueDisplay) dueDisplay.innerText = `₹${balanceDue.toFixed(2)}`;
}

// Print invoice helper
function printInvoice() {
    window.print();
}
