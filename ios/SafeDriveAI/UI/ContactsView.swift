import SwiftUI

struct ContactsView: View {
    @EnvironmentObject private var account: AccountManager

    @State private var contacts: [EmergencyContactDTO] = []
    @State private var showAddSheet = false
    @State private var isLoading = false
    @State private var errorMessage: String?

    var body: some View {
        Form {
            if !account.isAuthenticated {
                Section {
                    NavigationLink("Log In / Sign Up") { AccountView() }
                } footer: {
                    Text("An account is needed so contacts can be texted from your name.")
                }
            } else {
                Section {
                    if isLoading && contacts.isEmpty {
                        ProgressView()
                    } else if contacts.isEmpty {
                        Text("No trusted contacts yet.")
                            .foregroundStyle(.secondary)
                    } else {
                        ForEach(contacts) { contact in
                            VStack(alignment: .leading) {
                                Text(contact.name)
                                Text(contact.phoneNumber)
                                    .font(.footnote)
                                    .foregroundStyle(.secondary)
                            }
                        }
                        .onDelete(perform: delete)
                    }
                    Button("Add Contact") { showAddSheet = true }
                } header: {
                    Text("Trusted Contacts")
                } footer: {
                    Text("These contacts will receive a text message if you're detected as continuously distracted for about 10 seconds while driving.")
                }

                if let errorMessage {
                    Section {
                        Text(errorMessage)
                            .foregroundStyle(Theme.warning)
                    }
                }
            }
        }
        .navigationTitle("Trusted Contacts")
        .navigationBarTitleDisplayMode(.inline)
        .task { await refresh() }
        .refreshable { await refresh() }
        .sheet(isPresented: $showAddSheet) {
            AddContactView { newContact in
                contacts.append(newContact)
            }
        }
    }

    private func refresh() async {
        guard account.isAuthenticated else { return }
        isLoading = true
        defer { isLoading = false }
        do {
            contacts = try await APIClient.shared.fetchContacts()
            errorMessage = nil
        } catch {
            errorMessage = "Couldn't load contacts."
            await account.refreshAuthState()
        }
    }

    private func delete(at offsets: IndexSet) {
        let toDelete = offsets.map { contacts[$0] }
        contacts.remove(atOffsets: offsets)
        Task {
            for contact in toDelete {
                try? await APIClient.shared.deleteContact(id: contact.id)
            }
        }
    }
}
