import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:local_auth/local_auth.dart';
import 'package:geolocator/geolocator.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'dart:io';
import 'dart:math';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:device_info_plus/device_info_plus.dart';
import 'package:crypto/crypto.dart';

void main() {
  runApp(const SecureBankApp());
}

class SecureBankApp extends StatelessWidget {
  const SecureBankApp({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'SecureBank Mobile',
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.blue),
        useMaterial3: true,
      ),
      home: const LoginPage(),
    );
  }
}

// User Management Class
class UserManager {
  static const String _usersKey = 'registered_users';
  static const String _currentUserKey = 'current_user';

  static Future<bool> registerUser(
    String username,
    String password,
    String email,
  ) async {
    SharedPreferences prefs = await SharedPreferences.getInstance();
    List<String> users = prefs.getStringList(_usersKey) ?? [];

    // Check if user already exists
    for (String userData in users) {
      Map<String, dynamic> user = json.decode(userData);
      if (user['username'] == username || user['email'] == email) {
        return false; // User already exists
      }
    }

    // Hash password for security
    var bytes = utf8.encode(password);
    var digest = sha256.convert(bytes);

    Map<String, dynamic> newUser = {
      'username': username,
      'password': digest.toString(),
      'email': email,
      'created_at': DateTime.now().toIso8601String(),
      'user_id': DateTime.now().millisecondsSinceEpoch.toString(),
    };

    users.add(json.encode(newUser));
    await prefs.setStringList(_usersKey, users);
    return true;
  }

  static Future<Map<String, dynamic>?> loginUser(
    String username,
    String password,
  ) async {
    SharedPreferences prefs = await SharedPreferences.getInstance();
    List<String> users = prefs.getStringList(_usersKey) ?? [];

    // Hash input password
    var bytes = utf8.encode(password);
    var digest = sha256.convert(bytes);

    for (String userData in users) {
      Map<String, dynamic> user = json.decode(userData);
      if ((user['username'] == username || user['email'] == username) &&
          user['password'] == digest.toString()) {
        // Save current user
        await prefs.setString(_currentUserKey, userData);
        return user;
      }
    }
    return null;
  }

  static Future<Map<String, dynamic>?> getCurrentUser() async {
    SharedPreferences prefs = await SharedPreferences.getInstance();
    String? userData = prefs.getString(_currentUserKey);
    if (userData != null) {
      return json.decode(userData);
    }
    return null;
  }

  static Future<void> logoutUser() async {
    SharedPreferences prefs = await SharedPreferences.getInstance();
    await prefs.remove(_currentUserKey);
  }

  // Debug method to view all registered users
  static Future<void> printAllUsers() async {
    SharedPreferences prefs = await SharedPreferences.getInstance();
    List<String> users = prefs.getStringList(_usersKey) ?? [];

    print('=== REGISTERED USERS DEBUG ===');
    print('Total users: ${users.length}');

    for (int i = 0; i < users.length; i++) {
      Map<String, dynamic> user = json.decode(users[i]);
      print('User ${i + 1}:');
      print('  Username: ${user['username']}');
      print('  Email: ${user['email']}');
      print('  User ID: ${user['user_id']}');
      print('  Created: ${user['created_at']}');
      print('  Password Hash: ${user['password'].substring(0, 20)}...');
      print('---');
    }
    print('===============================');
  }

  // Method to clear all user data (for testing)
  static Future<void> clearAllUsers() async {
    SharedPreferences prefs = await SharedPreferences.getInstance();
    await prefs.remove(_usersKey);
    await prefs.remove(_currentUserKey);
    print('All user data cleared from SharedPreferences');
  }
}

// Login Page Class
class LoginPage extends StatefulWidget {
  const LoginPage({Key? key}) : super(key: key);

  @override
  State<LoginPage> createState() => _LoginPageState();
}

class _LoginPageState extends State<LoginPage> {
  final _formKey = GlobalKey<FormState>();
  final _usernameController = TextEditingController();
  final _passwordController = TextEditingController();
  final _emailController = TextEditingController();

  bool _isLogin = true;
  bool _isLoading = false;
  bool _obscurePassword = true;
  String _statusMessage = '';

  @override
  void dispose() {
    _usernameController.dispose();
    _passwordController.dispose();
    _emailController.dispose();
    super.dispose();
  }

  Future<void> _handleAuth() async {
    if (!_formKey.currentState!.validate()) return;

    setState(() {
      _isLoading = true;
      _statusMessage = '';
    });

    try {
      if (_isLogin) {
        // Login
        Map<String, dynamic>? user = await UserManager.loginUser(
          _usernameController.text.trim(),
          _passwordController.text,
        );

        if (user != null) {
          if (mounted) {
            Navigator.pushReplacement(
              context,
              MaterialPageRoute(builder: (context) => const BankHomePage()),
            );
          }
        } else {
          setState(() {
            _statusMessage = 'Invalid username/email or password';
          });
        }
      } else {
        // Register
        bool success = await UserManager.registerUser(
          _usernameController.text.trim(),
          _passwordController.text,
          _emailController.text.trim(),
        );

        if (success) {
          setState(() {
            _statusMessage = 'Registration successful! Please login.';
            _isLogin = true;
          });
          _clearForm();
        } else {
          setState(() {
            _statusMessage = 'Username or email already exists';
          });
        }
      }
    } catch (e) {
      setState(() {
        _statusMessage = 'An error occurred: $e';
      });
    } finally {
      setState(() {
        _isLoading = false;
      });
    }
  }

  void _clearForm() {
    _usernameController.clear();
    _passwordController.clear();
    _emailController.clear();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.grey[100],
      body: SafeArea(
        child: Center(
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(24.0),
            child: Form(
              key: _formKey,
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  // Bank Logo
                  Container(
                    width: 120,
                    height: 120,
                    decoration: BoxDecoration(
                      color: Colors.blue[700],
                      borderRadius: BorderRadius.circular(60),
                      boxShadow: [
                        BoxShadow(
                          color: Colors.blue.withOpacity(0.3),
                          spreadRadius: 2,
                          blurRadius: 10,
                          offset: const Offset(0, 4),
                        ),
                      ],
                    ),
                    child: const Icon(
                      Icons.account_balance,
                      size: 60,
                      color: Colors.white,
                    ),
                  ),
                  const SizedBox(height: 24),

                  // App Title
                  const Text(
                    'SecureBank Mobile',
                    style: TextStyle(
                      fontSize: 32,
                      fontWeight: FontWeight.bold,
                      color: Colors.black87,
                    ),
                  ),
                  const SizedBox(height: 8),
                  const Text(
                    'Your Security is Our Priority',
                    style: TextStyle(fontSize: 16, color: Colors.grey),
                  ),
                  const SizedBox(height: 40),

                  // Login/Register Toggle
                  Container(
                    decoration: BoxDecoration(
                      color: Colors.grey[200],
                      borderRadius: BorderRadius.circular(25),
                    ),
                    child: Row(
                      children: [
                        Expanded(
                          child: GestureDetector(
                            onTap: () => setState(() {
                              _isLogin = true;
                              _statusMessage = '';
                              _clearForm();
                            }),
                            child: Container(
                              padding: const EdgeInsets.symmetric(vertical: 12),
                              decoration: BoxDecoration(
                                color: _isLogin
                                    ? Colors.blue[700]
                                    : Colors.transparent,
                                borderRadius: BorderRadius.circular(25),
                              ),
                              child: Text(
                                'Login',
                                textAlign: TextAlign.center,
                                style: TextStyle(
                                  color: _isLogin
                                      ? Colors.white
                                      : Colors.grey[600],
                                  fontWeight: FontWeight.w600,
                                ),
                              ),
                            ),
                          ),
                        ),
                        Expanded(
                          child: GestureDetector(
                            onTap: () => setState(() {
                              _isLogin = false;
                              _statusMessage = '';
                              _clearForm();
                            }),
                            child: Container(
                              padding: const EdgeInsets.symmetric(vertical: 12),
                              decoration: BoxDecoration(
                                color: !_isLogin
                                    ? Colors.blue[700]
                                    : Colors.transparent,
                                borderRadius: BorderRadius.circular(25),
                              ),
                              child: Text(
                                'Register',
                                textAlign: TextAlign.center,
                                style: TextStyle(
                                  color: !_isLogin
                                      ? Colors.white
                                      : Colors.grey[600],
                                  fontWeight: FontWeight.w600,
                                ),
                              ),
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 32),

                  // Form Fields
                  Container(
                    padding: const EdgeInsets.all(24),
                    decoration: BoxDecoration(
                      color: Colors.white,
                      borderRadius: BorderRadius.circular(16),
                      boxShadow: [
                        BoxShadow(
                          color: Colors.grey.withOpacity(0.1),
                          spreadRadius: 1,
                          blurRadius: 10,
                          offset: const Offset(0, 4),
                        ),
                      ],
                    ),
                    child: Column(
                      children: [
                        // Username/Email Field
                        TextFormField(
                          controller: _usernameController,
                          decoration: InputDecoration(
                            labelText: _isLogin
                                ? 'Username or Email'
                                : 'Username',
                            prefixIcon: const Icon(Icons.person),
                            border: OutlineInputBorder(
                              borderRadius: BorderRadius.circular(12),
                            ),
                            filled: true,
                            fillColor: Colors.grey[50],
                          ),
                          validator: (value) {
                            if (value == null || value.trim().isEmpty) {
                              return 'Please enter your ${_isLogin ? 'username or email' : 'username'}';
                            }
                            return null;
                          },
                        ),
                        const SizedBox(height: 16),

                        // Email Field (only for registration)
                        if (!_isLogin) ...[
                          TextFormField(
                            controller: _emailController,
                            decoration: InputDecoration(
                              labelText: 'Email',
                              prefixIcon: const Icon(Icons.email),
                              border: OutlineInputBorder(
                                borderRadius: BorderRadius.circular(12),
                              ),
                              filled: true,
                              fillColor: Colors.grey[50],
                            ),
                            validator: (value) {
                              if (value == null || value.trim().isEmpty) {
                                return 'Please enter your email';
                              }
                              if (!RegExp(
                                r'^[\w-\.]+@([\w-]+\.)+[\w-]{2,4}$',
                              ).hasMatch(value)) {
                                return 'Please enter a valid email';
                              }
                              return null;
                            },
                          ),
                          const SizedBox(height: 16),
                        ],

                        // Password Field
                        TextFormField(
                          controller: _passwordController,
                          obscureText: _obscurePassword,
                          decoration: InputDecoration(
                            labelText: 'Password',
                            prefixIcon: const Icon(Icons.lock),
                            suffixIcon: IconButton(
                              icon: Icon(
                                _obscurePassword
                                    ? Icons.visibility
                                    : Icons.visibility_off,
                              ),
                              onPressed: () => setState(
                                () => _obscurePassword = !_obscurePassword,
                              ),
                            ),
                            border: OutlineInputBorder(
                              borderRadius: BorderRadius.circular(12),
                            ),
                            filled: true,
                            fillColor: Colors.grey[50],
                          ),
                          validator: (value) {
                            if (value == null || value.isEmpty) {
                              return 'Please enter your password';
                            }
                            if (!_isLogin && value.length < 6) {
                              return 'Password must be at least 6 characters';
                            }
                            return null;
                          },
                        ),
                        const SizedBox(height: 24),

                        // Status Message
                        if (_statusMessage.isNotEmpty) ...[
                          Container(
                            padding: const EdgeInsets.all(12),
                            decoration: BoxDecoration(
                              color: _statusMessage.contains('successful')
                                  ? Colors.green[50]
                                  : Colors.red[50],
                              borderRadius: BorderRadius.circular(8),
                              border: Border.all(
                                color: _statusMessage.contains('successful')
                                    ? Colors.green[300]!
                                    : Colors.red[300]!,
                              ),
                            ),
                            child: Text(
                              _statusMessage,
                              style: TextStyle(
                                color: _statusMessage.contains('successful')
                                    ? Colors.green[700]
                                    : Colors.red[700],
                                fontWeight: FontWeight.w500,
                              ),
                              textAlign: TextAlign.center,
                            ),
                          ),
                          const SizedBox(height: 16),
                        ],

                        // Submit Button
                        SizedBox(
                          width: double.infinity,
                          child: ElevatedButton(
                            onPressed: _isLoading ? null : _handleAuth,
                            style: ElevatedButton.styleFrom(
                              backgroundColor: Colors.blue[700],
                              foregroundColor: Colors.white,
                              padding: const EdgeInsets.symmetric(vertical: 16),
                              shape: RoundedRectangleBorder(
                                borderRadius: BorderRadius.circular(12),
                              ),
                              elevation: 2,
                            ),
                            child: _isLoading
                                ? const SizedBox(
                                    height: 20,
                                    width: 20,
                                    child: CircularProgressIndicator(
                                      strokeWidth: 2,
                                      valueColor: AlwaysStoppedAnimation<Color>(
                                        Colors.white,
                                      ),
                                    ),
                                  )
                                : Text(
                                    _isLogin ? 'Login' : 'Register',
                                    style: const TextStyle(
                                      fontSize: 16,
                                      fontWeight: FontWeight.bold,
                                    ),
                                  ),
                          ),
                        ),
                      ],
                    ),
                  ),

                  const SizedBox(height: 24),

                  // Debug Buttons (for development)
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                    children: [
                      TextButton(
                        onPressed: () async {
                          await UserManager.printAllUsers();
                          setState(() {
                            _statusMessage = 'Check console for user data';
                          });
                        },
                        child: const Text(
                          'View Users',
                          style: TextStyle(fontSize: 12),
                        ),
                      ),
                      TextButton(
                        onPressed: () async {
                          await UserManager.clearAllUsers();
                          setState(() {
                            _statusMessage = 'All user data cleared';
                          });
                        },
                        child: const Text(
                          'Clear Data',
                          style: TextStyle(fontSize: 12, color: Colors.red),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 16),

                  // Additional Info
                  Text(
                    _isLogin
                        ? "Don't have an account? Tap Register above"
                        : "Already have an account? Tap Login above",
                    style: TextStyle(color: Colors.grey[600], fontSize: 14),
                    textAlign: TextAlign.center,
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}

class BankHomePage extends StatefulWidget {
  const BankHomePage({Key? key}) : super(key: key);

  @override
  State<BankHomePage> createState() => _BankHomePageState();
}

class _BankHomePageState extends State<BankHomePage> {
  bool _authenticated = false;
  bool _fingerprintRegistered = false;
  String _authStatus = 'Waiting for authentication...';
  String _locationInfo = '';
  String _geoIpInfo = '';
  String _simInfo = '';
  bool _simVerified = false;
  final LocalAuthentication auth = LocalAuthentication();

  // SIM Change Detection Variables
  String _currentSimSerial = '';
  String _currentCarrierName = '';
  String _currentImei = '';
  Map<String, dynamic>? _simChangeAlert;
  double _simRiskScore = 0.0;

  // Location Discrepancy Score System
  List<Map<String, dynamic>> _sessionData = [];
  double _currentDiscrepancyScore = 0.0;
  Map<String, dynamic>? _currentGpsLocation;
  Map<String, dynamic>? _currentIpLocation;
  Map<String, dynamic>? _simActivationLocation;

  @override
  void initState() {
    super.initState();
    _loadSessionData();
    _checkBiometricStatus();
    _checkLocationAndGeoIP();
    _checkDeviceInfo();
    _checkSimInfo();
  }

  // Location Discrepancy Score System Methods
  Future<void> _loadSessionData() async {
    SharedPreferences prefs = await SharedPreferences.getInstance();
    String? sessionDataJson = prefs.getString('session_data');
    if (sessionDataJson != null) {
      List<dynamic> decodedData = json.decode(sessionDataJson);
      _sessionData = decodedData.cast<Map<String, dynamic>>();
    }

    // Load SIM activation location (set on first device registration)
    String? simLocationJson = prefs.getString('sim_activation_location');
    if (simLocationJson != null) {
      _simActivationLocation = json.decode(simLocationJson);
    }
  }

  Future<void> _saveSessionData() async {
    SharedPreferences prefs = await SharedPreferences.getInstance();
    await prefs.setString('session_data', json.encode(_sessionData));

    if (_simActivationLocation != null) {
      await prefs.setString(
        'sim_activation_location',
        json.encode(_simActivationLocation!),
      );
    }
  }

  double _calculateDistance(
    double lat1,
    double lon1,
    double lat2,
    double lon2,
  ) {
    // Using Haversine formula to calculate distance between two points
    const double earthRadius = 6371; // Earth's radius in kilometers

    double dLat = _toRadians(lat2 - lat1);
    double dLon = _toRadians(lon2 - lon1);

    double a =
        sin(dLat / 2) * sin(dLat / 2) +
        cos(_toRadians(lat1)) *
            cos(_toRadians(lat2)) *
            sin(dLon / 2) *
            sin(dLon / 2);

    double c = 2 * atan2(sqrt(a), sqrt(1 - a));
    return earthRadius * c;
  }

  double _toRadians(double degrees) {
    return degrees * pi / 180;
  }

  double _calculateLocationDiscrepancyScore() {
    if (_currentGpsLocation == null || _currentIpLocation == null) {
      return 0.0;
    }

    double score = 0.0;

    // 1. Distance between GPS and IP location (0-40 points)
    double gpsIpDistance = _calculateDistance(
      _currentGpsLocation!['latitude'],
      _currentGpsLocation!['longitude'],
      _currentIpLocation!['latitude'],
      _currentIpLocation!['longitude'],
    );

    double gpsIpScore = (gpsIpDistance / 10).clamp(
      0,
      40,
    ); // Max 40 points for >100km difference
    score += gpsIpScore;

    // 2. Distance from SIM activation location (0-30 points)
    if (_simActivationLocation != null) {
      double simGpsDistance = _calculateDistance(
        _simActivationLocation!['latitude'],
        _simActivationLocation!['longitude'],
        _currentGpsLocation!['latitude'],
        _currentGpsLocation!['longitude'],
      );

      double simScore = (simGpsDistance / 20).clamp(
        0,
        30,
      ); // Max 30 points for >600km difference
      score += simScore;
    }

    // 3. Frequency of location changes (0-30 points)
    double locationChangeScore = _calculateLocationChangeFrequency();
    score += locationChangeScore;

    return score.clamp(0, 100);
  }

  double _calculateLocationChangeFrequency() {
    if (_sessionData.length < 2) return 0.0;

    int significantChanges = 0;
    const double significantDistanceThreshold = 50; // 50km

    for (int i = 1; i < _sessionData.length; i++) {
      var currentSession = _sessionData[i];
      var previousSession = _sessionData[i - 1];

      if (currentSession['gps_location'] != null &&
          previousSession['gps_location'] != null) {
        double distance = _calculateDistance(
          currentSession['gps_location']['latitude'],
          currentSession['gps_location']['longitude'],
          previousSession['gps_location']['latitude'],
          previousSession['gps_location']['longitude'],
        );

        if (distance > significantDistanceThreshold) {
          significantChanges++;
        }
      }
    }

    // Score based on frequency of changes (more changes = higher score)
    double changeRate = significantChanges / _sessionData.length;
    return (changeRate * 30).clamp(0, 30);
  }

  String _getSecurityRiskLevel(double score) {
    if (score < 20) return "🟢 LOW";
    if (score < 50) return "🟡 MEDIUM";
    if (score < 80) return "🟠 HIGH";
    return "🔴 CRITICAL";
  }

  Future<void> _recordCurrentSession() async {
    String sessionId = 'S${DateTime.now().millisecondsSinceEpoch}';
    String userId = 'U123'; // In real app, get from user authentication

    Map<String, dynamic> sessionRecord = {
      'session_id': sessionId,
      'user_id': userId,
      'gps_location': _currentGpsLocation,
      'ip_location': _currentIpLocation,
      'sim_activation_location': _simActivationLocation,
      'timestamp': DateTime.now().toIso8601String(),
      'discrepancy_score': _currentDiscrepancyScore,
    };

    _sessionData.add(sessionRecord);

    // Keep only last 20 sessions to prevent excessive storage
    if (_sessionData.length > 20) {
      _sessionData = _sessionData.sublist(_sessionData.length - 20);
    }

    await _saveSessionData();
  }

  void _showLocationDiscrepancyDialog() {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('🔍 Location Discrepancy Analysis'),
        content: SizedBox(
          width: double.maxFinite,
          height: 400,
          child: Column(
            children: [
              // Current Score Card
              Container(
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: _getCurrentScoreColor(),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Column(
                  children: [
                    Text(
                      'Current Risk Score',
                      style: const TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.bold,
                        color: Colors.white,
                      ),
                    ),
                    const SizedBox(height: 8),
                    Text(
                      '${_currentDiscrepancyScore.toStringAsFixed(1)}/100',
                      style: const TextStyle(
                        fontSize: 24,
                        fontWeight: FontWeight.bold,
                        color: Colors.white,
                      ),
                    ),
                    Text(
                      _getSecurityRiskLevel(_currentDiscrepancyScore),
                      style: const TextStyle(fontSize: 14, color: Colors.white),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 16),

              // Session Data Table
              const Text(
                'Recent Sessions',
                style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 8),

              Expanded(
                child: _sessionData.isEmpty
                    ? const Center(child: Text('No session data available'))
                    : SingleChildScrollView(
                        scrollDirection: Axis.horizontal,
                        child: SingleChildScrollView(
                          child: DataTable(
                            columnSpacing: 8,
                            columns: const [
                              DataColumn(
                                label: Text(
                                  'Session',
                                  style: TextStyle(fontSize: 10),
                                ),
                              ),
                              DataColumn(
                                label: Text(
                                  'GPS',
                                  style: TextStyle(fontSize: 10),
                                ),
                              ),
                              DataColumn(
                                label: Text(
                                  'IP',
                                  style: TextStyle(fontSize: 10),
                                ),
                              ),
                              DataColumn(
                                label: Text(
                                  'Score',
                                  style: TextStyle(fontSize: 10),
                                ),
                              ),
                              DataColumn(
                                label: Text(
                                  'Time',
                                  style: TextStyle(fontSize: 10),
                                ),
                              ),
                            ],
                            rows: _sessionData.take(10).map((session) {
                              String sessionId =
                                  session['session_id']?.substring(
                                    session['session_id'].length - 4,
                                  ) ??
                                  'N/A';
                              String gpsLocation = _formatLocation(
                                session['gps_location'],
                              );
                              String ipLocation = _formatLocation(
                                session['ip_location'],
                              );
                              String score =
                                  session['discrepancy_score']?.toStringAsFixed(
                                    1,
                                  ) ??
                                  '0.0';
                              String time = _formatTime(session['timestamp']);

                              return DataRow(
                                cells: [
                                  DataCell(
                                    Text(
                                      sessionId,
                                      style: const TextStyle(fontSize: 9),
                                    ),
                                  ),
                                  DataCell(
                                    Text(
                                      gpsLocation,
                                      style: const TextStyle(fontSize: 8),
                                    ),
                                  ),
                                  DataCell(
                                    Text(
                                      ipLocation,
                                      style: const TextStyle(fontSize: 8),
                                    ),
                                  ),
                                  DataCell(
                                    Container(
                                      padding: const EdgeInsets.symmetric(
                                        horizontal: 4,
                                        vertical: 2,
                                      ),
                                      decoration: BoxDecoration(
                                        color: _getScoreColor(
                                          double.tryParse(score) ?? 0.0,
                                        ),
                                        borderRadius: BorderRadius.circular(4),
                                      ),
                                      child: Text(
                                        score,
                                        style: const TextStyle(
                                          fontSize: 8,
                                          color: Colors.white,
                                        ),
                                      ),
                                    ),
                                  ),
                                  DataCell(
                                    Text(
                                      time,
                                      style: const TextStyle(fontSize: 8),
                                    ),
                                  ),
                                ],
                              );
                            }).toList(),
                          ),
                        ),
                      ),
              ),
            ],
          ),
        ),
        actions: [
          TextButton(
            onPressed: () async {
              // Clear session data for testing
              _sessionData.clear();
              await _saveSessionData();
              Navigator.of(context).pop();
              setState(() {});
            },
            child: const Text('Clear Data'),
          ),
          TextButton(
            onPressed: () => Navigator.of(context).pop(),
            child: const Text('Close'),
          ),
        ],
      ),
    );
  }

  Color _getCurrentScoreColor() {
    if (_currentDiscrepancyScore < 20) return Colors.green;
    if (_currentDiscrepancyScore < 50) return Colors.orange;
    if (_currentDiscrepancyScore < 80) return Colors.red;
    return Colors.purple;
  }

  Color _getScoreColor(double score) {
    if (score < 20) return Colors.green;
    if (score < 50) return Colors.orange;
    if (score < 80) return Colors.red;
    return Colors.purple;
  }

  String _formatLocation(Map<String, dynamic>? location) {
    if (location == null) return 'N/A';
    double lat = location['latitude'] ?? 0.0;
    double lon = location['longitude'] ?? 0.0;
    return '${lat.toStringAsFixed(2)}, ${lon.toStringAsFixed(2)}';
  }

  String _formatTime(String? timestamp) {
    if (timestamp == null) return 'N/A';
    try {
      DateTime dt = DateTime.parse(timestamp);
      return '${dt.hour.toString().padLeft(2, '0')}:${dt.minute.toString().padLeft(2, '0')}';
    } catch (e) {
      return 'N/A';
    }
  }

  Future<void> _checkDeviceInfo() async {
    try {
      DeviceInfoPlugin deviceInfo = DeviceInfoPlugin();

      if (Platform.isAndroid) {
        AndroidDeviceInfo androidInfo = await deviceInfo.androidInfo;

        // Create a unique device fingerprint
        String deviceFingerprint =
            '${androidInfo.id}-${androidInfo.model}-${androidInfo.brand}-${androidInfo.device}';

        setState(() {
          _simInfo = 'Device ID: ${androidInfo.id}';
        });

        // Check stored device info
        SharedPreferences prefs = await SharedPreferences.getInstance();
        String? storedDeviceInfo = prefs.getString('device_fingerprint');

        if (storedDeviceInfo == null) {
          // First time user - store device info
          await prefs.setString('device_fingerprint', deviceFingerprint);
          await prefs.setString(
            'first_registration_date',
            DateTime.now().toIso8601String(),
          );
          setState(() {
            _simVerified = true;
            _authStatus =
                'Device registered successfully. Ready for authentication.';
          });
        } else if (storedDeviceInfo == deviceFingerprint) {
          // Same device - allow access
          setState(() {
            _simVerified = true;
          });
        } else {
          // Different device - deny access
          setState(() {
            _simVerified = false;
            _authStatus =
                'SECURITY ALERT: Different device detected. Access denied.';
          });
        }
      } else {
        // For iOS or other platforms
        setState(() {
          _simInfo = 'Device check bypassed (iOS/Other platform)';
          _simVerified = true;
        });
      }
    } catch (e) {
      setState(() {
        _simInfo = 'Device Error: $e';
        _simVerified = true; // Allow access for testing
      });
    }
  }

  // SIM Change Detection Methods
  Future<void> _checkSimInfo() async {
    try {
      if (Platform.isAndroid) {
        // Get device info for IMEI
        DeviceInfoPlugin deviceInfo = DeviceInfoPlugin();
        AndroidDeviceInfo androidInfo = await deviceInfo.androidInfo;
        _currentImei = androidInfo.id;

        // Simulate SIM info gathering (since real SIM APIs may need special permissions)
        _currentSimSerial = 'SIM_${DateTime.now().millisecondsSinceEpoch}';
        _currentCarrierName = await _getCarrierName();

        // Check for SIM changes
        await _detectSimChanges();
      } else {
        setState(() {
          _simInfo = '${_simInfo}\nSIM check bypassed (iOS/Other platform)';
        });
      }
    } catch (e) {
      setState(() {
        _simInfo = '${_simInfo}\nSIM Check Error: $e';
      });
    }
  }

  Future<String> _getCarrierName() async {
    try {
      // Simulate carrier detection - in a real app you'd use telephony APIs
      List<String> carriers = [
        'Verizon',
        'AT&T',
        'T-Mobile',
        'Sprint',
        'Other',
      ];
      return carriers[Random().nextInt(carriers.length)];
    } catch (e) {
      return 'Unknown Carrier';
    }
  }

  Future<void> _detectSimChanges() async {
    try {
      SharedPreferences prefs = await SharedPreferences.getInstance();

      // Get stored SIM info
      String? storedSimSerial = prefs.getString('stored_sim_serial');
      String? storedCarrier = prefs.getString('stored_carrier');
      String? storedImei = prefs.getString('stored_imei');
      String? lastSimChangeTime = prefs.getString('last_sim_change_time');

      Map<String, dynamic> currentSimData = {
        'sim_serial': _currentSimSerial,
        'carrier': _currentCarrierName,
        'imei': _currentImei,
        'timestamp': DateTime.now().toIso8601String(),
      };

      double riskScore = 0.0;
      List<String> alerts = [];

      // First time setup
      if (storedSimSerial == null) {
        await prefs.setString('stored_sim_serial', _currentSimSerial);
        await prefs.setString('stored_carrier', _currentCarrierName);
        await prefs.setString('stored_imei', _currentImei);
        await prefs.setString(
          'last_sim_change_time',
          DateTime.now().toIso8601String(),
        );

        setState(() {
          _simInfo = '${_simInfo}\n🟢 SIM Registered: $_currentCarrierName';
        });
        return;
      }

      // Check for SIM serial change (High Risk)
      if (storedSimSerial != _currentSimSerial) {
        riskScore += 60.0;
        alerts.add('🔴 SIM Card Changed');

        // Check time since last change
        if (lastSimChangeTime != null) {
          DateTime lastChange = DateTime.parse(lastSimChangeTime);
          Duration timeDiff = DateTime.now().difference(lastChange);

          if (timeDiff.inDays < 7) {
            riskScore += 30.0;
            alerts.add('⚠️ Frequent SIM Changes (< 7 days)');
          }
        }

        // Update stored SIM info
        await prefs.setString('stored_sim_serial', _currentSimSerial);
        await prefs.setString(
          'last_sim_change_time',
          DateTime.now().toIso8601String(),
        );
      }

      // Check for carrier change with same SIM (Medium Risk)
      if (storedSimSerial == _currentSimSerial &&
          storedCarrier != _currentCarrierName) {
        riskScore += 25.0;
        alerts.add('🟡 Carrier Changed');
        await prefs.setString('stored_carrier', _currentCarrierName);
      }

      // Check for IMEI change (Critical Risk)
      if (storedImei != _currentImei) {
        riskScore += 40.0;
        alerts.add('🔴 Device IMEI Changed');
        await prefs.setString('stored_imei', _currentImei);
      }

      // Store SIM change data for analysis
      String? simHistoryJson = prefs.getString('sim_change_history');
      List<Map<String, dynamic>> simHistory = [];
      if (simHistoryJson != null) {
        List<dynamic> decodedHistory = json.decode(simHistoryJson);
        simHistory = decodedHistory.cast<Map<String, dynamic>>();
      }

      if (alerts.isNotEmpty) {
        simHistory.add({
          'timestamp': DateTime.now().toIso8601String(),
          'alerts': alerts,
          'risk_score': riskScore,
          'sim_data': currentSimData,
        });

        // Keep only last 10 SIM change records
        if (simHistory.length > 10) {
          simHistory = simHistory.sublist(simHistory.length - 10);
        }

        await prefs.setString('sim_change_history', json.encode(simHistory));
      }

      // Update state
      setState(() {
        _simRiskScore = riskScore;
        _simChangeAlert = alerts.isNotEmpty
            ? {
                'alerts': alerts,
                'risk_score': riskScore,
                'timestamp': DateTime.now().toIso8601String(),
              }
            : null;

        if (alerts.isNotEmpty) {
          _simInfo =
              '${_simInfo}\n${alerts.join(', ')} (Risk: ${riskScore.toStringAsFixed(1)})';
        } else {
          _simInfo = '${_simInfo}\n🟢 SIM Verified: $_currentCarrierName';
        }
      });

      // Additional security measures for high risk
      if (riskScore > 50.0) {
        setState(() {
          _simVerified = false;
          _authStatus =
              'SECURITY ALERT: SIM change detected. Access restricted.';
        });
      }
    } catch (e) {
      setState(() {
        _simInfo = '${_simInfo}\nSIM Detection Error: $e';
      });
    }
  }

  void _showSimChangeDialog() {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('📱 SIM Change Detection'),
        content: SizedBox(
          width: double.maxFinite,
          height: 300,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Current SIM Info
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: Colors.blue[50],
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(color: Colors.blue[200]!),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      'Current SIM Info',
                      style: TextStyle(
                        fontSize: 14,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    const SizedBox(height: 8),
                    Text(
                      'Carrier: $_currentCarrierName',
                      style: const TextStyle(fontSize: 12),
                    ),
                    Text(
                      'Serial: ${_currentSimSerial.substring(0, min(20, _currentSimSerial.length))}...',
                      style: const TextStyle(fontSize: 12),
                    ),
                    Text(
                      'IMEI: ${_currentImei.substring(0, min(15, _currentImei.length))}...',
                      style: const TextStyle(fontSize: 12),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 16),

              // Risk Score
              if (_simRiskScore > 0) ...[
                Container(
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: _getSimRiskColor().withOpacity(0.1),
                    borderRadius: BorderRadius.circular(8),
                    border: Border.all(color: _getSimRiskColor()),
                  ),
                  child: Row(
                    children: [
                      Icon(
                        _getSimRiskIcon(),
                        color: _getSimRiskColor(),
                        size: 20,
                      ),
                      const SizedBox(width: 8),
                      Text(
                        'SIM Risk Score: ${_simRiskScore.toStringAsFixed(1)}/100',
                        style: TextStyle(
                          fontWeight: FontWeight.bold,
                          color: _getSimRiskColor(),
                        ),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 16),
              ],

              // Recent Alerts
              if (_simChangeAlert != null) ...[
                const Text(
                  'Recent Alerts',
                  style: TextStyle(fontSize: 14, fontWeight: FontWeight.bold),
                ),
                const SizedBox(height: 8),
                ...(_simChangeAlert!['alerts'] as List<String>).map(
                  (alert) => Padding(
                    padding: const EdgeInsets.symmetric(vertical: 2),
                    child: Row(
                      children: [
                        const Icon(
                          Icons.warning,
                          color: Colors.orange,
                          size: 16,
                        ),
                        const SizedBox(width: 8),
                        Expanded(
                          child: Text(
                            alert,
                            style: const TextStyle(fontSize: 12),
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
              ] else ...[
                const Row(
                  children: [
                    Icon(Icons.check_circle, color: Colors.green, size: 20),
                    SizedBox(width: 8),
                    Text('No SIM security alerts'),
                  ],
                ),
              ],
            ],
          ),
        ),
        actions: [
          TextButton(
            onPressed: () async {
              // Reset SIM history for testing
              SharedPreferences prefs = await SharedPreferences.getInstance();
              await prefs.remove('stored_sim_serial');
              await prefs.remove('stored_carrier');
              await prefs.remove('stored_imei');
              await prefs.remove('sim_change_history');
              Navigator.of(context).pop();
              _checkSimInfo();
            },
            child: const Text('Reset SIM Data'),
          ),
          TextButton(
            onPressed: () => Navigator.of(context).pop(),
            child: const Text('Close'),
          ),
        ],
      ),
    );
  }

  Color _getSimRiskColor() {
    if (_simRiskScore < 25) return Colors.green;
    if (_simRiskScore < 50) return Colors.orange;
    return Colors.red;
  }

  IconData _getSimRiskIcon() {
    if (_simRiskScore < 25) return Icons.check_circle;
    if (_simRiskScore < 50) return Icons.warning;
    return Icons.error;
  }

  Future<void> _checkLocationAndGeoIP() async {
    await _getCurrentLocation();
    await _getGeoIPInfo();
  }

  Future<void> _getCurrentLocation() async {
    try {
      // Request location permission
      LocationPermission permission = await Geolocator.requestPermission();

      if (permission == LocationPermission.denied ||
          permission == LocationPermission.deniedForever) {
        setState(() {
          _locationInfo = 'Location permission denied';
        });
        return;
      }

      // Get current position
      Position position = await Geolocator.getCurrentPosition(
        desiredAccuracy: LocationAccuracy.high,
      );

      // Store GPS location data
      _currentGpsLocation = {
        'latitude': position.latitude,
        'longitude': position.longitude,
        'accuracy': position.accuracy,
        'timestamp': DateTime.now().toIso8601String(),
      };

      setState(() {
        _locationInfo =
            'GPS: ${position.latitude.toStringAsFixed(4)}, ${position.longitude.toStringAsFixed(4)}';
      });

      // Set SIM activation location on first registration
      SharedPreferences prefs = await SharedPreferences.getInstance();
      if (_simActivationLocation == null &&
          prefs.getString('sim_activation_location') == null) {
        _simActivationLocation = {
          'latitude': position.latitude,
          'longitude': position.longitude,
          'timestamp': DateTime.now().toIso8601String(),
        };
        await _saveSessionData();
      }

      // Update discrepancy score
      _updateDiscrepancyScore();
    } catch (e) {
      setState(() {
        _locationInfo = 'GPS Error: $e';
      });
    }
  }

  Future<void> _getGeoIPInfo() async {
    try {
      final response = await http.get(
        Uri.parse('https://ipapi.co/json/'),
        headers: {'User-Agent': 'Calculator App'},
      );

      if (response.statusCode == 200) {
        final data = json.decode(response.body);

        // Store IP location data
        _currentIpLocation = {
          'latitude': double.tryParse(data['latitude'].toString()) ?? 0.0,
          'longitude': double.tryParse(data['longitude'].toString()) ?? 0.0,
          'city': data['city'],
          'country': data['country_name'],
          'ip': data['ip'],
          'timestamp': DateTime.now().toIso8601String(),
        };

        setState(() {
          _geoIpInfo =
              'IP Location: ${data['city']}, ${data['country_name']} (${data['ip']})';
        });

        // Update discrepancy score
        _updateDiscrepancyScore();
      } else {
        setState(() {
          _geoIpInfo = 'Geo-IP: Unable to fetch location';
        });
      }
    } catch (e) {
      setState(() {
        _geoIpInfo = 'Geo-IP Error: $e';
      });
    }
  }

  void _updateDiscrepancyScore() {
    if (_currentGpsLocation != null && _currentIpLocation != null) {
      _currentDiscrepancyScore = _calculateLocationDiscrepancyScore();
      setState(() {});
    }
  }

  Future<void> _checkBiometricStatus() async {
    try {
      final bool isAvailable = await auth.isDeviceSupported();
      final bool canCheckBiometrics = await auth.canCheckBiometrics;
      final List<BiometricType> availableBiometrics = await auth
          .getAvailableBiometrics();

      setState(() {
        _fingerprintRegistered = availableBiometrics.isNotEmpty;
        if (!isAvailable || !canCheckBiometrics) {
          _authStatus = 'Biometric authentication not available';
        } else if (!_fingerprintRegistered) {
          _authStatus = 'No fingerprints registered on device';
        } else {
          _authStatus = 'Ready for authentication';
        }
      });
    } catch (e) {
      setState(() {
        _authStatus = 'Error checking biometric status: $e';
      });
    }
  }

  Future<void> _authenticate() async {
    // First check if SIM is verified
    if (!_simVerified) {
      setState(() {
        _authStatus = 'Access denied: SIM card verification failed.';
      });
      return;
    }

    bool authenticated = false;
    try {
      // Check if biometric authentication is available
      final bool isAvailable = await auth.isDeviceSupported();
      final bool canCheckBiometrics = await auth.canCheckBiometrics;

      if (!isAvailable || !canCheckBiometrics) {
        setState(() {
          _authStatus = 'Biometric authentication not supported on this device';
        });
        return;
      }

      final List<BiometricType> availableBiometrics = await auth
          .getAvailableBiometrics();

      if (availableBiometrics.isEmpty) {
        setState(() {
          _authStatus =
              'No biometrics enrolled. Please register your fingerprint in device settings.';
        });
        return;
      }

      setState(() {
        _authStatus = 'Authenticating...';
      });

      authenticated = await auth.authenticate(
        localizedReason: 'Please authenticate to access the calculator',
        options: const AuthenticationOptions(
          biometricOnly: false, // Allow PIN/password as fallback
          stickyAuth: true,
        ),
      );

      if (authenticated) {
        // Record current session for location tracking
        await _recordCurrentSession();

        setState(() {
          _authStatus = 'Authentication successful!';
          _authenticated = true;
        });
      } else {
        setState(() {
          _authStatus = 'Authentication failed. Please try again.';
        });
      }
    } on PlatformException catch (e) {
      setState(() {
        if (e.code == 'no_fragment_activity') {
          _authStatus = 'App configuration error. Please restart the app.';
        } else if (e.code == 'NotAvailable') {
          _authStatus =
              'Biometric authentication is not available on this device';
        } else if (e.code == 'NotEnrolled') {
          _authStatus =
              'No biometrics enrolled. Please set up fingerprint in device settings.';
        } else {
          _authStatus = 'Authentication error: ${e.message}';
        }
      });
    } catch (e) {
      setState(() {
        _authStatus = 'Authentication error: $e';
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    if (!_authenticated) {
      return Scaffold(
        appBar: AppBar(
          title: const Text('SecureBank Login'),
          backgroundColor: Theme.of(context).colorScheme.primary,
        ),
        body: Center(
          child: Padding(
            padding: const EdgeInsets.all(24.0),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                // Bank Logo
                Container(
                  width: 120,
                  height: 120,
                  decoration: BoxDecoration(
                    color: Colors.blue[700],
                    borderRadius: BorderRadius.circular(60),
                  ),
                  child: const Icon(
                    Icons.account_balance,
                    size: 60,
                    color: Colors.white,
                  ),
                ),
                const SizedBox(height: 24),
                const Text(
                  'SecureBank Mobile',
                  style: TextStyle(fontSize: 28, fontWeight: FontWeight.bold),
                ),
                const SizedBox(height: 8),
                const Text(
                  'Your Security is Our Priority',
                  style: TextStyle(fontSize: 16, color: Colors.grey),
                ),
                const SizedBox(height: 32),
                Icon(
                  _fingerprintRegistered ? Icons.fingerprint : Icons.warning,
                  size: 48,
                  color: _fingerprintRegistered ? Colors.blue : Colors.orange,
                ),
                const SizedBox(height: 16),
                Text(
                  _authStatus,
                  style: const TextStyle(fontSize: 16),
                  textAlign: TextAlign.center,
                ),
                const SizedBox(height: 16),
                // Security Information Card
                Container(
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: Colors.grey[50],
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(color: Colors.grey[300]!),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          Icon(
                            Icons.security,
                            color: Colors.blue[700],
                            size: 20,
                          ),
                          const SizedBox(width: 8),
                          const Text(
                            'Security Status',
                            style: TextStyle(
                              fontSize: 16,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 12),
                      _buildSecurityItem(
                        Icons.location_on,
                        'Location',
                        _locationInfo.isEmpty ? 'Verifying...' : _locationInfo,
                        _locationInfo.isNotEmpty,
                      ),
                      _buildSecurityItem(
                        Icons.public,
                        'Network',
                        _geoIpInfo.isEmpty ? 'Checking...' : _geoIpInfo,
                        _geoIpInfo.isNotEmpty,
                      ),
                      _buildSecurityItem(
                        Icons.phonelink_setup,
                        'Device',
                        _simInfo.isEmpty ? 'Validating...' : _simInfo,
                        _simVerified,
                      ),
                      _buildSecurityItem(
                        Icons.sim_card,
                        'SIM Security',
                        _simRiskScore > 0
                            ? 'Risk Score: ${_simRiskScore.toStringAsFixed(1)}/100'
                            : 'SIM Verified',
                        _simRiskScore < 50,
                      ),
                      if (_currentDiscrepancyScore > 0) ...[
                        const SizedBox(height: 8),
                        Container(
                          padding: const EdgeInsets.symmetric(
                            horizontal: 12,
                            vertical: 6,
                          ),
                          decoration: BoxDecoration(
                            color: _getCurrentScoreColor(),
                            borderRadius: BorderRadius.circular(6),
                          ),
                          child: Row(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              const Icon(
                                Icons.analytics,
                                color: Colors.white,
                                size: 16,
                              ),
                              const SizedBox(width: 8),
                              Text(
                                'Risk Score: ${_currentDiscrepancyScore.toStringAsFixed(1)}/100 ${_getSecurityRiskLevel(_currentDiscrepancyScore)}',
                                style: const TextStyle(
                                  fontSize: 12,
                                  color: Colors.white,
                                  fontWeight: FontWeight.bold,
                                ),
                              ),
                            ],
                          ),
                        ),
                      ],
                    ],
                  ),
                ),
                const SizedBox(height: 32),
                if (_fingerprintRegistered && _simVerified) ...[
                  SizedBox(
                    width: double.infinity,
                    child: ElevatedButton.icon(
                      icon: const Icon(Icons.fingerprint, size: 28),
                      label: const Text(
                        'Secure Login',
                        style: TextStyle(
                          fontSize: 18,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                      onPressed: _authenticate,
                      style: ElevatedButton.styleFrom(
                        padding: const EdgeInsets.symmetric(vertical: 16),
                        backgroundColor: Colors.blue[700],
                        foregroundColor: Colors.white,
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(12),
                        ),
                      ),
                    ),
                  ),
                ] else if (!_simVerified) ...[
                  SizedBox(
                    width: double.infinity,
                    child: ElevatedButton.icon(
                      icon: const Icon(Icons.block, size: 28),
                      label: const Text(
                        'Access Blocked - Security Alert',
                        style: TextStyle(
                          fontSize: 16,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                      onPressed: null,
                      style: ElevatedButton.styleFrom(
                        padding: const EdgeInsets.symmetric(vertical: 16),
                        backgroundColor: Colors.red[700],
                        foregroundColor: Colors.white,
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(12),
                        ),
                      ),
                    ),
                  ),
                  const SizedBox(height: 16),
                  TextButton(
                    onPressed: () async {
                      SharedPreferences prefs =
                          await SharedPreferences.getInstance();
                      await prefs.remove('device_fingerprint');
                      _checkDeviceInfo();
                    },
                    child: const Text(
                      'Reset Device Registration (Admin Only)',
                      style: TextStyle(color: Colors.grey),
                    ),
                  ),
                ] else ...[
                  const Text(
                    'Biometric Authentication Required',
                    style: TextStyle(fontSize: 16, fontWeight: FontWeight.w600),
                  ),
                  const SizedBox(height: 12),
                  const Text(
                    'Please enable fingerprint or face recognition in your device settings to continue.',
                    style: TextStyle(fontSize: 14, color: Colors.grey),
                    textAlign: TextAlign.center,
                  ),
                  const SizedBox(height: 16),
                  ElevatedButton.icon(
                    icon: const Icon(Icons.refresh),
                    label: const Text('Check Again'),
                    onPressed: _checkBiometricStatus,
                    style: ElevatedButton.styleFrom(
                      padding: const EdgeInsets.symmetric(
                        horizontal: 24,
                        vertical: 12,
                      ),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(8),
                      ),
                    ),
                  ),
                ],
              ],
            ),
          ),
        ),
      );
    }

    // Banking App Interface After Authentication
    return Scaffold(
      appBar: AppBar(
        title: const Text('SecureBank'),
        backgroundColor: Colors.blue[700],
        foregroundColor: Colors.white,
        elevation: 0,
        actions: [
          IconButton(
            icon: const Icon(Icons.analytics),
            onPressed: () => _showLocationDiscrepancyDialog(),
            tooltip: 'Location Analytics',
          ),
          IconButton(
            icon: const Icon(Icons.sim_card),
            onPressed: () => _showSimChangeDialog(),
            tooltip: 'SIM Analytics',
          ),
          IconButton(
            icon: const Icon(Icons.notifications_outlined),
            onPressed: () => _showNotifications(),
            tooltip: 'Notifications',
          ),
          IconButton(
            icon: const Icon(Icons.logout),
            onPressed: () async {
              await UserManager.logoutUser();
              if (mounted) {
                Navigator.pushReplacement(
                  context,
                  MaterialPageRoute(builder: (context) => const LoginPage()),
                );
              }
            },
            tooltip: 'Logout',
          ),
        ],
      ),
      body: Column(
        children: [
          // Account Balance Header
          Container(
            width: double.infinity,
            padding: const EdgeInsets.all(24),
            decoration: BoxDecoration(
              gradient: LinearGradient(
                begin: Alignment.topCenter,
                end: Alignment.bottomCenter,
                colors: [Colors.blue[700]!, Colors.blue[500]!],
              ),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  'Welcome back, John',
                  style: TextStyle(fontSize: 18, color: Colors.white70),
                ),
                const SizedBox(height: 8),
                const Text(
                  'Total Balance',
                  style: TextStyle(fontSize: 14, color: Colors.white70),
                ),
                const SizedBox(height: 4),
                const Text(
                  '\$25,430.50',
                  style: TextStyle(
                    fontSize: 36,
                    fontWeight: FontWeight.bold,
                    color: Colors.white,
                  ),
                ),
                const SizedBox(height: 16),
                if (_currentDiscrepancyScore > 0)
                  Container(
                    padding: const EdgeInsets.symmetric(
                      horizontal: 12,
                      vertical: 6,
                    ),
                    decoration: BoxDecoration(
                      color: _getCurrentScoreColor().withOpacity(0.2),
                      borderRadius: BorderRadius.circular(6),
                      border: Border.all(color: Colors.white30),
                    ),
                    child: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        const Icon(
                          Icons.security,
                          color: Colors.white,
                          size: 16,
                        ),
                        const SizedBox(width: 8),
                        Text(
                          'Security Score: ${_getSecurityRiskLevel(_currentDiscrepancyScore)}',
                          style: const TextStyle(
                            fontSize: 12,
                            color: Colors.white,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                      ],
                    ),
                  ),
              ],
            ),
          ),

          // Quick Actions
          Padding(
            padding: const EdgeInsets.all(16),
            child: Row(
              children: [
                Expanded(
                  child: _buildQuickAction(
                    Icons.send,
                    'Transfer',
                    () => _showTransferDialog(),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: _buildQuickAction(
                    Icons.payment,
                    'Pay Bills',
                    () => _showPayBillsDialog(),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: _buildQuickAction(
                    Icons.account_balance_wallet,
                    'Deposit',
                    () => _showDepositDialog(),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: _buildQuickAction(
                    Icons.more_horiz,
                    'More',
                    () => _showMoreOptions(),
                  ),
                ),
              ],
            ),
          ),

          // Accounts Section
          Expanded(
            child: SingleChildScrollView(
              padding: const EdgeInsets.symmetric(horizontal: 16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text(
                    'Your Accounts',
                    style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
                  ),
                  const SizedBox(height: 16),

                  _buildAccountCard(
                    'Checking Account',
                    '**** 1234',
                    '\$8,430.50',
                    Icons.account_balance,
                    Colors.blue,
                  ),
                  const SizedBox(height: 12),

                  _buildAccountCard(
                    'Savings Account',
                    '**** 5678',
                    '\$15,000.00',
                    Icons.savings,
                    Colors.green,
                  ),
                  const SizedBox(height: 12),

                  _buildAccountCard(
                    'Credit Card',
                    '**** 9012',
                    '\$2,000.00',
                    Icons.credit_card,
                    Colors.orange,
                  ),

                  const SizedBox(height: 24),

                  const Text(
                    'Recent Transactions',
                    style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
                  ),
                  const SizedBox(height: 16),

                  _buildTransactionItem(
                    'Grocery Store',
                    'Aug 4, 2025',
                    '-\$85.23',
                    Icons.shopping_cart,
                    Colors.red,
                  ),
                  _buildTransactionItem(
                    'Salary Deposit',
                    'Aug 1, 2025',
                    '+\$3,500.00',
                    Icons.work,
                    Colors.green,
                  ),
                  _buildTransactionItem(
                    'Netflix Subscription',
                    'Jul 30, 2025',
                    '-\$15.99',
                    Icons.movie,
                    Colors.red,
                  ),
                  _buildTransactionItem(
                    'ATM Withdrawal',
                    'Jul 28, 2025',
                    '-\$100.00',
                    Icons.atm,
                    Colors.red,
                  ),

                  const SizedBox(height: 20),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildSecurityItem(
    IconData icon,
    String title,
    String subtitle,
    bool isVerified,
  ) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        children: [
          Icon(
            icon,
            size: 16,
            color: isVerified ? Colors.green : Colors.orange,
          ),
          const SizedBox(width: 8),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  title,
                  style: const TextStyle(
                    fontSize: 12,
                    fontWeight: FontWeight.w500,
                  ),
                ),
                Text(
                  subtitle,
                  style: const TextStyle(fontSize: 10, color: Colors.grey),
                  overflow: TextOverflow.ellipsis,
                ),
              ],
            ),
          ),
          Icon(
            isVerified ? Icons.check_circle : Icons.pending,
            size: 16,
            color: isVerified ? Colors.green : Colors.orange,
          ),
        ],
      ),
    );
  }

  Widget _buildQuickAction(IconData icon, String label, VoidCallback onTap) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: Colors.grey[50],
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: Colors.grey[200]!),
        ),
        child: Column(
          children: [
            Icon(icon, size: 28, color: Colors.blue[700]),
            const SizedBox(height: 8),
            Text(
              label,
              style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w500),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildAccountCard(
    String title,
    String accountNumber,
    String balance,
    IconData icon,
    Color color,
  ) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: Colors.grey[200]!),
        boxShadow: [
          BoxShadow(
            color: Colors.grey.withOpacity(0.1),
            spreadRadius: 1,
            blurRadius: 3,
            offset: const Offset(0, 1),
          ),
        ],
      ),
      child: Row(
        children: [
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: color.withOpacity(0.1),
              borderRadius: BorderRadius.circular(8),
            ),
            child: Icon(icon, color: color, size: 24),
          ),
          const SizedBox(width: 16),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  title,
                  style: const TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.w600,
                  ),
                ),
                Text(
                  accountNumber,
                  style: const TextStyle(fontSize: 14, color: Colors.grey),
                ),
              ],
            ),
          ),
          Text(
            balance,
            style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
          ),
        ],
      ),
    );
  }

  Widget _buildTransactionItem(
    String title,
    String date,
    String amount,
    IconData icon,
    Color amountColor,
  ) {
    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: Colors.grey[50],
        borderRadius: BorderRadius.circular(8),
      ),
      child: Row(
        children: [
          Container(
            padding: const EdgeInsets.all(8),
            decoration: BoxDecoration(
              color: Colors.grey[200],
              borderRadius: BorderRadius.circular(6),
            ),
            child: Icon(icon, size: 20, color: Colors.grey[600]),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  title,
                  style: const TextStyle(
                    fontSize: 14,
                    fontWeight: FontWeight.w500,
                  ),
                ),
                Text(
                  date,
                  style: const TextStyle(fontSize: 12, color: Colors.grey),
                ),
              ],
            ),
          ),
          Text(
            amount,
            style: TextStyle(
              fontSize: 14,
              fontWeight: FontWeight.bold,
              color: amountColor,
            ),
          ),
        ],
      ),
    );
  }

  // Banking App Methods
  void _showNotifications() {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('🔔 Notifications'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            _buildNotificationItem(
              Icons.security,
              'Security Alert',
              'New login detected from your current location',
              '2 min ago',
            ),
            _buildNotificationItem(
              Icons.payment,
              'Payment Received',
              'Salary deposit of \$3,500.00',
              '3 days ago',
            ),
            _buildNotificationItem(
              Icons.warning,
              'Location Security',
              'Risk Score: ${_getSecurityRiskLevel(_currentDiscrepancyScore)}',
              'Now',
            ),
            if (_simChangeAlert != null)
              _buildNotificationItem(
                Icons.sim_card,
                'SIM Security Alert',
                'Risk Score: ${_simRiskScore.toStringAsFixed(1)}/100',
                'Now',
              ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(),
            child: const Text('Close'),
          ),
        ],
      ),
    );
  }

  Widget _buildNotificationItem(
    IconData icon,
    String title,
    String subtitle,
    String time,
  ) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 8),
      child: Row(
        children: [
          Icon(icon, color: Colors.blue[700], size: 20),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  title,
                  style: const TextStyle(
                    fontWeight: FontWeight.w600,
                    fontSize: 14,
                  ),
                ),
                Text(
                  subtitle,
                  style: const TextStyle(fontSize: 12, color: Colors.grey),
                ),
                Text(
                  time,
                  style: const TextStyle(fontSize: 10, color: Colors.grey),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  void _showTransferDialog() {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('💸 Transfer Money'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const TextField(
              decoration: InputDecoration(
                labelText: 'Recipient Account',
                border: OutlineInputBorder(),
              ),
            ),
            const SizedBox(height: 16),
            const TextField(
              decoration: InputDecoration(
                labelText: 'Amount (\$)',
                border: OutlineInputBorder(),
              ),
              keyboardType: TextInputType.number,
            ),
            const SizedBox(height: 16),
            Text(
              'Security Score: ${_getSecurityRiskLevel(_currentDiscrepancyScore)}',
              style: TextStyle(
                color: _getCurrentScoreColor(),
                fontWeight: FontWeight.bold,
              ),
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(),
            child: const Text('Cancel'),
          ),
          ElevatedButton(
            onPressed: () {
              Navigator.of(context).pop();
              _showTransferSuccess();
            },
            child: const Text('Transfer'),
          ),
        ],
      ),
    );
  }

  void _showTransferSuccess() {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('✅ Transfer Successful'),
        content: const Text('Your transfer has been processed successfully.'),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(),
            child: const Text('OK'),
          ),
        ],
      ),
    );
  }

  void _showPayBillsDialog() {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('📄 Pay Bills'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            _buildBillItem('Electricity Bill', '\$85.50'),
            _buildBillItem('Internet Bill', '\$49.99'),
            _buildBillItem('Phone Bill', '\$35.00'),
            _buildBillItem('Credit Card', '\$120.00'),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(),
            child: const Text('Close'),
          ),
        ],
      ),
    );
  }

  Widget _buildBillItem(String title, String amount) {
    return Container(
      margin: const EdgeInsets.symmetric(vertical: 4),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        border: Border.all(color: Colors.grey[300]!),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(title, style: const TextStyle(fontWeight: FontWeight.w500)),
          Text(amount, style: const TextStyle(fontWeight: FontWeight.bold)),
        ],
      ),
    );
  }

  void _showDepositDialog() {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('💰 Deposit Money'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const TextField(
              decoration: InputDecoration(
                labelText: 'Amount (\$)',
                border: OutlineInputBorder(),
              ),
              keyboardType: TextInputType.number,
            ),
            const SizedBox(height: 16),
            const TextField(
              decoration: InputDecoration(
                labelText: 'Reference (Optional)',
                border: OutlineInputBorder(),
              ),
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(),
            child: const Text('Cancel'),
          ),
          ElevatedButton(
            onPressed: () {
              Navigator.of(context).pop();
              _showDepositSuccess();
            },
            child: const Text('Deposit'),
          ),
        ],
      ),
    );
  }

  void _showDepositSuccess() {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('✅ Deposit Successful'),
        content: const Text('Your deposit has been processed successfully.'),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(),
            child: const Text('OK'),
          ),
        ],
      ),
    );
  }

  void _showMoreOptions() {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('⚙️ More Options'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            _buildMoreOption(Icons.settings, 'Account Settings'),
            _buildMoreOption(Icons.help, 'Help & Support'),
            _buildMoreOption(Icons.security, 'Security Settings'),
            _buildMoreOption(Icons.analytics, 'View Location Analytics'),
            _buildMoreOption(Icons.sim_card, 'View SIM Analytics'),
            _buildMoreOption(Icons.receipt_long, 'Transaction History'),
            _buildMoreOption(Icons.account_circle, 'Profile Management'),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(),
            child: const Text('Close'),
          ),
        ],
      ),
    );
  }

  Widget _buildMoreOption(IconData icon, String title) {
    return GestureDetector(
      onTap: () {
        Navigator.of(context).pop();
        if (title == 'View Location Analytics') {
          _showLocationDiscrepancyDialog();
        } else if (title == 'View SIM Analytics') {
          _showSimChangeDialog();
        }
      },
      child: Container(
        margin: const EdgeInsets.symmetric(vertical: 4),
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(
          border: Border.all(color: Colors.grey[300]!),
          borderRadius: BorderRadius.circular(8),
        ),
        child: Row(
          children: [
            Icon(icon, color: Colors.blue[700], size: 20),
            const SizedBox(width: 12),
            Text(title, style: const TextStyle(fontWeight: FontWeight.w500)),
          ],
        ),
      ),
    );
  }
}
