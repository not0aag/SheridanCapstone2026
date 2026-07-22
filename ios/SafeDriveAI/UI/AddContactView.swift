import SwiftUI

struct AddContactView: View {
    @Environment(\.dismiss) private var dismiss
    /// Reports the entered fields to the caller, which owns the store. Kept
    /// closure-based (rather than touching the store directly) so the sheet
    /// stays a pure form and doesn't depend on how contacts are persisted.
    let onAdd: (_ name: String, _ phoneNumber: String, _ email: String?) -> Void

    @State private var name = ""
    @State private var phoneNumber = ""
    @State private var email = ""

    var body: some View {
        NavigationStack {
            Form {
                Section {
                    TextField("Name", text: $name)
                        .textContentType(.name)
                    TextField("Phone number", text: $phoneNumber)
                        .textContentType(.telephoneNumber)
                        .keyboardType(.phonePad)
                    TextField("Email (optional)", text: $email)
                        .textContentType(.emailAddress)
                        .keyboardType(.emailAddress)
                        .textInputAutocapitalization(.never)
                        .autocorrectionDisabled()
                }
            }
            .navigationTitle("Add Contact")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Cancel") { dismiss() }
                }
                ToolbarItem(placement: .confirmationAction) {
                    Button("Save") { save() }
                        .disabled(name.isEmpty || phoneNumber.isEmpty)
                }
            }
        }
    }

    private func save() {
        onAdd(name, phoneNumber, email.isEmpty ? nil : email)
        dismiss()
    }
}
