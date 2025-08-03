// This is a basic Flutter widget test.
//
// To perform an interaction with a widget in your test, use the WidgetTester
// utility in the flutter_test package. For example, you can send tap and scroll
// gestures. You can also use WidgetTester to find child widgets in the widget
// tree, read text, and verify that the values of widget properties are correct.

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:secure_bank_mobile/main.dart';

void main() {
  testWidgets('Bank app authentication test', (WidgetTester tester) async {
    // Build our app and trigger a frame.
    await tester.pumpWidget(const SecureBankApp());

    // Verify that the app shows the SecureBank login screen
    expect(find.text('SecureBank Mobile'), findsOneWidget);
    expect(find.text('Your Security is Our Priority'), findsOneWidget);
    
    // Verify that the login button or biometric elements are present
    expect(find.byIcon(Icons.account_balance), findsOneWidget);
  });
}
