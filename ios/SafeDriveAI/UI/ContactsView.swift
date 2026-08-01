import SwiftUI

/// The people SafeDrive will offer to text if a distraction episode drags on.
///
/// No account required. This screen used to hide everything behind a
/// sign-up, which was left over from the server-backed design: contacts once
/// lived on the backend and were texted by it. They don't any more — they're
/// stored on this device and the message goes out through Apple's own
/// composer from the driver's own number. Asking someone to invent a
/// password before they can name an emergency contact was pure friction
/// guarding nothing, and the safety feature most worth having set up is the
/// one people actually finish setting up.
struct ContactsView: View {
    @EnvironmentObject private var contactsStore: LocalContactsStore

    @State private var showAddSheet = false

    var body: some View {
        Form {
            Section {
                if contactsStore.contacts.isEmpty {
                    Text("No trusted contacts yet.")
                        .foregroundStyle(Theme.textSecondary)
                } else {
                    ForEach(contactsStore.contacts) { contact in
                        VStack(alignment: .leading, spacing: 2) {
                            Text(contact.name)
                            Text(contact.phoneNumber)
                                .font(.sdMeta)
                                .foregroundStyle(Theme.textSecondary)
                        }
                        .accessibilityElement(children: .combine)
                    }
                    .onDelete(perform: delete)
                }
                Button("Add contact") { showAddSheet = true }
            } header: {
                Text("Trusted contacts").sdSectionLabel()
            } footer: {
                Text("If you stay distracted for about 10 seconds, SafeDrive opens a message to these contacts with the text already written. You review it and press send — nothing is sent automatically, and their numbers never leave this phone.")
            }
            .listRowBackground(Theme.surface)
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
