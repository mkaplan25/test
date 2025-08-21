import 'package:flutter/material.dart';
import 'package:webview_flutter/webview_flutter.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';

class PhaseDiagramScreen extends StatefulWidget {
  @override
  _PhaseDiagramScreenState createState() => _PhaseDiagramScreenState();
}

class _PhaseDiagramScreenState extends State<PhaseDiagramScreen> {
  late WebViewController _controller;
  String selectedElement = 'C';
  String xAxisType = 'mol';
  String yAxisType = 'celsius';
  List<String> availableElements = [];
  bool isLoading = false;
  String baseUrl = 'http://127.0.0.1:8000'; // Sunucu IP'nizi buraya yazın

  @override
  void initState() {
    super.initState();
    _initializeWebView();
    _loadAvailableElements();
  }

  void _initializeWebView() {
    _controller = WebViewController()
      ..setJavaScriptMode(JavaScriptMode.unrestricted)
      //..setBackgroundColor(Colors.white)
      ..setNavigationDelegate(
        NavigationDelegate(
          onProgress: (int progress) {
            debugPrint('WebView is loading (progress : $progress%)');
          },
          onPageStarted: (String url) {
            debugPrint('Page started loading: $url');
          },
          onPageFinished: (String url) {
            debugPrint('Page finished loading: $url');
          },
          onWebResourceError: (WebResourceError error) {
            debugPrint('''
Page resource error:
  code: ${error.errorCode}
  description: ${error.description}
  errorType: ${error.errorType}
  isForMainFrame: ${error.isForMainFrame}
            ''');
          },
        ),
      );
  }

  Future<void> _loadAvailableElements() async {
    try {
      final response = await http.get(Uri.parse('$baseUrl/elements'));
      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        setState(() {
          availableElements = List<String>.from(data['available_elements']);
          if (availableElements.isNotEmpty &&
              !availableElements.contains(selectedElement)) {
            selectedElement = availableElements.first;
          }
        });
        _loadDiagram();
      }
    } catch (e) {
      _showError('Element listesi yüklenemedi: $e');
    }
  }

  Future<void> _loadDiagram() async {
    setState(() {
      isLoading = true;
    });

    try {
      final url =
          '$baseUrl/generate-diagram/$selectedElement?x_axis=$xAxisType&y_axis=$yAxisType';
      await _controller.loadRequest(Uri.parse(url));
    } catch (e) {
      _showError('Diyagram yüklenemedi: $e');
    } finally {
      setState(() {
        isLoading = false;
      });
    }
  }

  void _showError(String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message),
        backgroundColor: Colors.red,
        duration: Duration(seconds: 3),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('Fe-${selectedElement} Faz Diyagramı'),
        backgroundColor: Colors.blue[700],
        foregroundColor: Colors.white,
        elevation: 0,
      ),
      body: Column(
        children: [
          // Kontrol Paneli
          Container(
            padding: EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: Colors.grey[100],
              border: Border(bottom: BorderSide(color: Colors.grey[300]!)),
            ),
            child: Column(
              children: [
                // Element Seçimi
                Row(
                  children: [
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text('Element:',
                              style: TextStyle(fontWeight: FontWeight.bold)),
                          SizedBox(height: 4),
                          DropdownButtonFormField<String>(
                            value: availableElements.contains(selectedElement)
                                ? selectedElement
                                : null,
                            decoration: InputDecoration(
                              border: OutlineInputBorder(),
                              contentPadding: EdgeInsets.symmetric(
                                  horizontal: 12, vertical: 8),
                            ),
                            items: availableElements.map((element) {
                              return DropdownMenuItem(
                                value: element,
                                child: Text('Fe-$element'),
                              );
                            }).toList(),
                            onChanged: (value) {
                              if (value != null) {
                                setState(() {
                                  selectedElement = value;
                                });
                                _loadDiagram();
                              }
                            },
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
                SizedBox(height: 16),
                // Eksen Seçimleri
                Row(
                  children: [
                    // X Ekseni
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text('X Ekseni:',
                              style: TextStyle(fontWeight: FontWeight.bold)),
                          SizedBox(height: 4),
                          DropdownButtonFormField<String>(
                            value: xAxisType,
                            decoration: InputDecoration(
                              border: OutlineInputBorder(),
                              contentPadding: EdgeInsets.symmetric(
                                  horizontal: 12, vertical: 8),
                            ),
                            items: [
                              DropdownMenuItem(
                                  value: 'mol', child: Text('Mol Fraksiyonu')),
                              DropdownMenuItem(
                                  value: 'wt', child: Text('Ağırlıkça %')),
                            ],
                            onChanged: (value) {
                              if (value != null) {
                                setState(() {
                                  xAxisType = value;
                                });
                                _loadDiagram();
                              }
                            },
                          ),
                        ],
                      ),
                    ),
                    SizedBox(width: 16),
                    // Y Ekseni
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text('Y Ekseni:',
                              style: TextStyle(fontWeight: FontWeight.bold)),
                          SizedBox(height: 4),
                          DropdownButtonFormField<String>(
                            value: yAxisType,
                            decoration: InputDecoration(
                              border: OutlineInputBorder(),
                              contentPadding: EdgeInsets.symmetric(
                                  horizontal: 12, vertical: 8),
                            ),
                            items: [
                              DropdownMenuItem(
                                  value: 'kelvin', child: Text('Kelvin')),
                              DropdownMenuItem(
                                  value: 'celsius', child: Text('Santigrat')),
                            ],
                            onChanged: (value) {
                              if (value != null) {
                                setState(() {
                                  yAxisType = value;
                                });
                                _loadDiagram();
                              }
                            },
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
                SizedBox(height: 16),
                // Yenile Butonu
                SizedBox(
                  width: double.infinity,
                  child: ElevatedButton.icon(
                    onPressed: isLoading ? null : _loadDiagram,
                    icon: Icon(Icons.refresh),
                    label:
                        Text(isLoading ? 'Yükleniyor...' : 'Diyagramı Yenile'),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: Colors.blue[700],
                      foregroundColor: Colors.white,
                      padding: EdgeInsets.symmetric(vertical: 12),
                    ),
                  ),
                ),
              ],
            ),
          ),
          // WebView
          Expanded(
            child: Stack(
              children: [
                WebViewWidget(controller: _controller),
                if (isLoading)
                  Container(
                    color: Colors.white.withOpacity(0.8),
                    child: Center(
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          CircularProgressIndicator(),
                          SizedBox(height: 16),
                          Text('Faz diyagramı oluşturuluyor...'),
                        ],
                      ),
                    ),
                  ),
              ],
            ),
          ),
        ],
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: () {
          showDialog(
            context: context,
            builder: (context) => AlertDialog(
              title: Text('Kullanım Bilgisi'),
              content: Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('🔍 Zoom yapabilirsiniz'),
                  Text('👆 Grafik üzerinde gezinebilirsiniz'),
                  Text('⚙️ Üstteki seçeneklerle diyagramı özelleştirin'),
                  Text('🔄 Yenile butonuyla diyagramı güncelleyin'),
                ],
              ),
              actions: [
                TextButton(
                  onPressed: () => Navigator.pop(context),
                  child: Text('Tamam'),
                ),
              ],
            ),
          );
        },
        child: Icon(Icons.help),
        backgroundColor: Colors.blue[700],
      ),
    );
  }
}

// Ana uygulama widget'ı
class MyApp extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Faz Diyagramı',
      theme: ThemeData(
        primarySwatch: Colors.blue,
        visualDensity: VisualDensity.adaptivePlatformDensity,
      ),
      home: PhaseDiagramScreen(),
      debugShowCheckedModeBanner: false,
    );
  }
}
