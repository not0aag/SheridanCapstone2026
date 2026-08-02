import SwiftUI
import MessageUI

/// The people SafeDrive will offer to text if a distraction episode drags on.
///
/// No account required — contacts are stored on this device and the message
/// goes out through Apple's own composer from the driver's own number.
///
/// This screen carries three things that used to make the feature look
/// "broken" when it wasn't, or genuinely was:
/// 1. The on/off switch lived only in Settings, several taps away from the
///    contacts it controls. A driver could add a contact, never see the
///    switch, and reasonably conclude the feature didn't work. It's here
///    now, directly above the list it governs.
/// 2. Confirming it actually works meant driving distracted for 10+ real
///    seconds. "Send test message" fires the same composer, the same
///    contacts, immediately — no detection, no waiting.
/// 3. `MFMessageComposeViewController` cannot send text at all on a device
///    without SMS/iMessage capability (the Simulator, a Wi-Fi-only iPad).
///    That used to fail silently — nothing presented, nothing explained.
///    Now it's a plain banner, checked up front rather than discovered by
///    a button that quietly does nothing.
struct ContactsView: View {
    @EnvironmentObject private var contactsStore: LocalContactsStore
    @EnvironmentObject private var settings: AppSettings
    @EnvironmentObject private var monitor: DriverMonitor

    @State private var showAddSheet = false
    @State private var testFeedback: TestFeedback?

    private enum TestFeedback: Identifiable {
        case sent
        case noContacts
        case cannotSend

        var id: Self { self }
    }

    private var canSendText: Bool { MFMessageComposeViewController.canSendText() }

    var body: some View {
        Form {
            if !canSendText {
                Section {
                    Label(
                        "This device can't send text messages, so alerts can't go out from it. This is a hardware/carrier limitation, not a setting — it won't work on the Simulator or a Wi-Fi-only iPad.",
                        systemImage: "exclamationmark.triangle.fill"
                    )
                    .font(.sdCaption)
                    .foregroundStyle(Theme.gold)
                }
                .listRowBackground(Theme.goldSoft)
            }

            Section {
                Toggle("Text trusted contacts when distracted", isOn: $settings.smsAlertsEnabled)
            } footer: {
                Text("If you stay distracted for about 10 seconds, SafeDrive opens a message to your contacts below with the text already written. You review it and press send — nothing is sent automatically, and their numbers never leave this phone.")
            }
            .listRowBackground(Theme.surface)

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
            }
            .listRowBackground(Theme.surface)

            if !contactsStore.contacts.isEmpty {
                Section {
                    Button("Send test message") {
                        Haptics.tap()
                        if monitor.sendTestMessage() {
                            testFeedback = .sent
                        } else {
                            testFeedback = canSendText ? .noContacts : .cannotSend
                        }
                    }
                    .disabled(!canSendText)
                } footer: {
                    Text("Sends the same composer, to the same contacts, right now — no need to wait for a real distraction alert to confirm this is set up correctly.")
                }
                .listRowBackground(Theme.surface)
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
        .alert(item: $testFeedback) { feedback in
            switch feedback {
            case .sent:
                Alert(title: Text("Message ready"), message: Text("Check that it opened behind this screen."))
            case .noContacts:
                Alert(title: Text("No contacts to message"))
            case .cannotSend:
                Alert(title: Text("Can't send from this device"),
                      message: Text("This device doesn't support sending text messages."))
            }
        }
    }

    private func delete(at offsets: IndexSet) {
        for contact in offsets.map({ contactsStore.contacts[$0] }) {
            contactsStore.delete(id: contact.id)
        }
    }
}
