import SwiftUI

struct AccountView: View {
    @EnvironmentObject private var account: AccountManager

    @State private var mode: Mode = .login
    @State private var email = ""
    @State private var password = ""
    @State private var fullName = ""
    @State private var isSubmitting = false

    private enum Mode: String, CaseIterable {
        case login = "Log In"
        case register = "Sign Up"
    }

    var body: some View {
        Form {
            Section {
                Picker("Mode", selection: $mode) {
                    ForEach(Mode.allCases, id: \.self) { Text($0.rawValue).tag($0) }
                }
                .pickerStyle(.segmented)
            }
            .listRowBackground(Color.clear)

            Section {
                if mode == .register {
                    TextField("Full name", text: $fullName)
                        .textContentType(.name)
                }
                TextField("Email", text: $email)
                    .textContentType(.emailAddress)
                    .keyboardType(.emailAddress)
                    .textInputAutocapitalization(.never)
                    .autocorrectionDisabled()
                SecureField("Password", text: $password)
                    .textContentType(mode == .register ? .newPassword : .password)
            } footer: {
                Text("Needed so your trusted contacts can be texted from your account when you're detected as distracted.")
            }

            if let error = account.lastErrorMessage {
                Section {
                    Text(error)
                        .foregroundStyle(Theme.warning)
                }
            }

            Section {
                Button {
                    submit()
                } label: {
                    if isSubmitting {
                        ProgressView()
                            .frame(maxWidth: .infinity)
                    } else {
                        Text(mode.rawValue)
                            .frame(maxWidth: .infinity)
                    }
                }
                .buttonStyle(BigButtonStyle())
                .disabled(!canSubmit || isSubmitting)
                .listRowInsets(EdgeInsets())
                .listRowBackground(Color.clear)
            }
        }
        .navigationTitle("Account")
        .navigationBarTitleDisplayMode(.inline)
    }

    private var canSubmit: Bool {
        !email.isEmpty && !password.isEmpty && (mode == .login || !fullName.isEmpty)
    }

    private func submit() {
        isSubmitting = true
        Task {
            let success: Bool
            switch mode {
            case .login:
                success = await account.login(email: email, password: password)
            case .register:
                success = await account.register(email: email, password: password, fullName: fullName)
            }
            isSubmitting = false
            if success { password = "" }
        }
    }
}
