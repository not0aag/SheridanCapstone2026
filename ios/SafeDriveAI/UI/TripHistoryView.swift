import SwiftUI

/// A driver's own trend over time — the same kind of history a fitness or
/// sleep-tracking app offers, not a demo screen.
///
/// Built on a real `List` rather than hand-rolled rows so swipe-to-delete,
/// Dynamic Type and VoiceOver's list semantics all come for free; the
/// Golden Hour look comes from hiding the system background and supplying
/// our own row fills.
struct TripHistoryView: View {
    @ObservedObject var tripLog: TripLog

    var body: some View {
        ZStack(alignment: .topTrailing) {
            Theme.background.ignoresSafeArea()

            Aura(size: 224)
                .offset(x: 60, y: 40)

            VStack(spacing: 0) {
                SDNavTitle("Trips")
                    .padding(.top, 8)

                if tripLog.trips.isEmpty {
                    emptyState
                } else {
                    tripList
                }
            }
        }
    }

    private var tripList: some View {
        List {
            Section {
                HStack(spacing: 10) {
                    StatCard(value: "\(averageScore)", label: "Avg score",
                             tint: averageScore >= 85 ? Theme.safe : Theme.gold)
                    StatCard(value: formattedTotalTime, label: "Monitored")
                    StatCard(value: "\(totalAlerts)", label: "Alerts")
                }
                .listRowInsets(EdgeInsets(top: 0, leading: 16, bottom: 8, trailing: 16))
                .listRowBackground(Color.clear)
                .listRowSeparator(.hidden)
            }

            Section {
                ForEach(tripLog.trips) { trip in
                    TripRow(trip: trip)
                        .listRowBackground(Theme.surface)
                        .listRowSeparatorTint(Theme.hairline)
                }
                .onDelete { offsets in
                    for index in offsets { tripLog.deleteTrip(id: tripLog.trips[index].id) }
                }
            }
        }
        .listStyle(.insetGrouped)
        .scrollContentBackground(.hidden)
        .environment(\.defaultMinListRowHeight, 44)
    }

    private var emptyState: some View {
        VStack(spacing: 12) {
            Spacer()
            Image(systemName: "road.lanes")
                .font(.system(size: 44))
                .foregroundStyle(Theme.textSecondary)
            Text("No trips yet")
                .font(.sdLead)
                .foregroundStyle(Theme.textPrimary)
            Text("Start monitoring a drive to see your history here.")
                .font(.sdCaption)
                .foregroundStyle(Theme.textSecondary)
                .multilineTextAlignment(.center)
                .padding(.horizontal, 48)
            Spacer()
            Spacer()
        }
        .frame(maxWidth: .infinity)
    }

    // MARK: Aggregates

    private var averageScore: Int {
        guard !tripLog.trips.isEmpty else { return 0 }
        return tripLog.trips.reduce(0) { $0 + $1.safetyScore } / tripLog.trips.count
    }

    private var totalAlerts: Int {
        tripLog.trips.reduce(0) { $0 + $1.drowsyAlertCount + $1.distractedAlertCount }
    }

    private var formattedTotalTime: String {
        let minutes = Int(tripLog.totalDrivingTime) / 60
        return minutes < 60 ? "\(minutes)m" : "\(minutes / 60)h"
    }
}

private struct TripRow: View {
    let trip: TripSummary

    var body: some View {
        HStack(spacing: 12) {
            VStack(alignment: .leading, spacing: 2) {
                Text(title)
                    .font(.sdRow)
                    .foregroundStyle(Theme.textPrimary)
                Text(meta)
                    .font(.sdMeta)
                    .foregroundStyle(Theme.textSecondary)
            }
            Spacer(minLength: 0)
            Text("\(trip.safetyScore)")
                .font(.system(size: 19, weight: .semibold))
                .monospacedDigit()
                .foregroundStyle(trip.safetyScore >= 85 ? Theme.safe : Theme.gold)
        }
        .padding(.vertical, 4)
        .accessibilityElement(children: .combine)
        .accessibilityLabel("\(title), \(meta), safety score \(trip.safetyScore)")
    }

    /// Derived from when the drive actually happened rather than stored —
    /// trips aren't named, and inventing one would be fiction.
    private var title: String {
        switch Calendar.current.component(.hour, from: trip.startedAt) {
        case 5..<12: "Morning drive"
        case 12..<17: "Afternoon drive"
        case 17..<22: "Evening drive"
        default: "Night drive"
        }
    }

    /// "Today · 6:15 PM · 42m"
    private var meta: String {
        let day: String
        if Calendar.current.isDateInToday(trip.startedAt) {
            day = "Today"
        } else if Calendar.current.isDateInYesterday(trip.startedAt) {
            day = "Yesterday"
        } else {
            day = trip.startedAt.formatted(.dateTime.weekday(.abbreviated))
        }
        let time = trip.startedAt.formatted(date: .omitted, time: .shortened)
        let minutes = Int(trip.duration) / 60
        let length = minutes < 60 ? "\(minutes)m" : "\(minutes / 60)h \(minutes % 60)m"
        return "\(day) · \(time) · \(length)"
    }
}
