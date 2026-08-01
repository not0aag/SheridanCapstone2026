import SwiftUI

struct ContactsView: View {
    @EnvironmentObject private var account: AccountManager
    @EnvironmentObject private var contactsStore: LocalContactsStore

    @State private var showAddSheet = false

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
                    if contactsStore.contacts.isEmpty {
                        Text("No trusted contacts yet.")
                            .foregroundStyle(.secondary)
                    } else {
                        ForEach(contactsStore.contacts) { contact in
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
            }
        }
        .scrollContentBackground(.hidden)
        .background(Theme.background)
        .navigationTitle("Trusted Contacts")
        .navigationBarTitleDisplayMode(.inline)
        .sheet(isPresented: $showAddSheet) {
            AddContactView { name, phoneNumber, email in
                contactsStore.add(name: name, phoneNumber: phoneNumber, email: email)
            }
        }
    }

    private func delete(at offsets: IndexSet) {
        for contact in offsets.map({ contactsStore.contacts[$0] }) {
            contactsStore.delete(id: contact.id)
        }
    }
}
