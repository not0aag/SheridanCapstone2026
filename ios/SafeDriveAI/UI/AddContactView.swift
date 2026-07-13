import SwiftUI

struct AddContactView: View {
    @Environment(\.dismiss) private var dismiss
    let onAdd: (EmergencyContactDTO) -> Void

    @State private var name = ""
    @State private var phoneNumber = ""
    @State private var email = ""
    @State private var isSaving = false
    @State private var errorMessage: String?

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

                if let errorMessage {
                    Section {
                        Text(errorMessage)
                            .foregroundStyle(Theme.warning)
                    }
                }
            }
            .navigationTitle("Add Contact")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Cancel") { dismiss() }
                }
                ToolbarItem(placement: .confirmationAction) {
                    if isSaving {
                        ProgressView()
                    } else {
                        Button("Save") { save() }
                            .disabled(name.isEmpty || phoneNumber.isEmpty)
                    }
                }
            }
        }
    }

    private func save() {
        isSaving = true
        Task {
            do {
                let contact = try await APIClient.shared.addContact(
                    name: name,
                    phoneNumber: phoneNumber,
                    email: email.isEmpty ? nil : email
                )
                onAdd(contact)
                dismiss()
            } catch {
                errorMessage = "Couldn't save contact. Check the phone number and try again."
                isSaving = false
            }
        }
    }
}
