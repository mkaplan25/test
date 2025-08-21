import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;

class TernaryDisplay extends StatefulWidget {
  final Map<String, dynamic> result;
  final List<Map<String, dynamic>>? elements;
  final double? temperature;

  const TernaryDisplay({
    Key? key,
    required this.result,
    this.elements,
    this.temperature,
  }) : super(key: key);

  @override
  State<TernaryDisplay> createState() => _TernaryDisplayState();
}

class _TernaryDisplayState extends State<TernaryDisplay> {
  String selectedDiagramType = 'isothermal'; // 'isothermal' veya 'vertical'
  bool isLoading = false;
  String? errorMessage;
  Map<String, dynamic>? currentDiagramData;

  // Sıcaklık aralığı için controller'lar
  final TextEditingController tempMinController =
      TextEditingController(text: '300');
  final TextEditingController tempMaxController =
      TextEditingController(text: '1800');

  @override
  @override
  void initState() {
    super.initState();

    // Eğer data nested ise çıkar
    if (widget.result.containsKey('result') && widget.result['result'] is Map) {
      currentDiagramData = Map<String, dynamic>.from(widget.result['result']);
    } else {
      currentDiagramData = widget.result;
    }

    // Backend'den gelen diagram tipini set et
    if (currentDiagramData != null &&
        currentDiagramData!.containsKey('diagram_type')) {
      selectedDiagramType = currentDiagramData!['diagram_type'];
    }

    // Debug
    print("currentDiagramData keys: ${currentDiagramData?.keys}");
    print("Selected diagram type from backend: $selectedDiagramType");
  }

  @override
  void dispose() {
    tempMinController.dispose();
    tempMaxController.dispose();
    super.dispose();
  }

  // Diagram tipini değiştir ve yeni hesaplama yap
  Future<void> _switchDiagramType(String newType,
      {bool forceRedraw = false}) async {
    print(
        "_switchDiagramType çağrıldı: $newType, forceRedraw: $forceRedraw"); // DEBUG

    if (newType == selectedDiagramType && !forceRedraw) return;

    setState(() {
      selectedDiagramType = newType;
      isLoading = true;
      errorMessage = null;
    });

    try {
      // Element bilgilerini widget.result'tan al
      List<Map<String, dynamic>> elements = [];
      double temperature = 1000.0;

      if (widget.elements != null && widget.elements!.isNotEmpty) {
        elements = widget.elements!;
      } else if (widget.result.containsKey('elements')) {
        elements = List<Map<String, dynamic>>.from(widget.result['elements']);
      }

      if (widget.temperature != null) {
        temperature = widget.temperature!;
      } else if (widget.result.containsKey('temperature')) {
        temperature = widget.result['temperature'].toDouble();
      }

      final nonFeElements = elements.where((e) => e['symbol'] != 'FE').toList();

      if (nonFeElements.length < 2) {
        throw Exception('En az 2 Fe olmayan element gerekli');
      }

      // Diagram tipine göre farklı parametreler hazırla
      Map<String, dynamic> requestBody = {
        'element1': nonFeElements[0]['symbol'],
        'element2': nonFeElements[1]['symbol'],
        'weight_percent1': nonFeElements[0]['weight_percent'],
        'weight_percent2': nonFeElements[1]['weight_percent'],
        'diagram_type': newType,
      };

      if (newType == 'isothermal') {
        requestBody['temperature_c'] = temperature;
        requestBody['pressure_pa'] = 101325.0;
        requestBody['step_size'] = 0.1;
      } else if (newType == 'vertical') {
        requestBody['temp_min'] =
            double.tryParse(tempMinController.text) ?? 300.0;
        requestBody['temp_max'] =
            double.tryParse(tempMaxController.text) ?? 1800.0;
      }

      // Backend'e yeni istek gönder
      final response = await http.post(
        Uri.parse('http://127.0.0.1:8000/ternary-diagram'),
        headers: {'Content-Type': 'application/json'},
        body: json.encode(requestBody),
      );

      if (response.statusCode == 200) {
        final Map<String, dynamic> data = json.decode(response.body);
        setState(() {
          isLoading = false;
          currentDiagramData = data;
        });
      } else {
        throw Exception('API hatası: ${response.statusCode}');
      }
    } catch (e) {
      setState(() {
        isLoading = false;
        errorMessage = 'Diagram değiştirme hatası: $e';
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Header
          Row(
            children: [
              Icon(Icons.change_history, color: Colors.blue, size: 24),
              SizedBox(width: 8),
              Text(
                'Ternary Phase Diagram',
                style: TextStyle(
                  fontSize: 20,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ],
          ),

          SizedBox(height: 16),

          // Radio Button Controls
          Card(
            child: Padding(
              padding: EdgeInsets.all(12),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Diagram Type:',
                    style: TextStyle(
                      fontWeight: FontWeight.bold,
                      fontSize: 16,
                    ),
                  ),
                  SizedBox(height: 8),
                  Row(
                    children: [
                      Expanded(
                        child: RadioListTile<String>(
                          title: Text('Isothermal'),
                          subtitle: Text('Sabit sıcaklık'),
                          value: 'isothermal',
                          groupValue: selectedDiagramType,
                          onChanged: isLoading
                              ? null
                              : (value) {
                                  if (value != null) {
                                    setState(() {
                                      selectedDiagramType = value;
                                    });
                                    // Isothermal seçilince otomatik çiz
                                    _switchDiagramType(value,
                                        forceRedraw: true);
                                  }
                                },
                          dense: true,
                        ),
                      ),
                      Expanded(
                        child: RadioListTile<String>(
                          title: Text('Vertical Section'),
                          subtitle: Text('Sıcaklık değişimi'),
                          value: 'vertical',
                          groupValue: selectedDiagramType,
                          onChanged: isLoading
                              ? null
                              : (value) {
                                  if (value != null) {
                                    setState(() {
                                      selectedDiagramType = value;
                                      currentDiagramData =
                                          null; // Mevcut grafiği temizle
                                    });
                                    // Vertical için otomatik çizim YOK
                                  }
                                },
                          dense: true,
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ),

          SizedBox(height: 16),

          // Vertical seçildiyse sıcaklık aralığı input'ları
          if (selectedDiagramType == 'vertical') ...[
            Card(
              child: Padding(
                padding: EdgeInsets.all(12),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'Sıcaklık Aralığı:',
                      style: TextStyle(
                        fontWeight: FontWeight.bold,
                        fontSize: 16,
                      ),
                    ),
                    SizedBox(height: 8),
                    Row(
                      children: [
                        Expanded(
                          child: TextField(
                            controller: tempMinController,
                            decoration: InputDecoration(
                              labelText: 'Minimum (°C)',
                              border: OutlineInputBorder(),
                              isDense: true,
                            ),
                            keyboardType: TextInputType.number,
                            onChanged: (value) {
                              // Değer değiştiğinde otomatik güncelleme yapılabilir
                            },
                          ),
                        ),
                        SizedBox(width: 12),
                        Expanded(
                          child: TextField(
                            controller: tempMaxController,
                            decoration: InputDecoration(
                              labelText: 'Maximum (°C)',
                              border: OutlineInputBorder(),
                              isDense: true,
                            ),
                            keyboardType: TextInputType.number,
                            onChanged: (value) {
                              // Değer değiştiğinde otomatik güncelleme yapılabilir
                            },
                          ),
                        ),
                      ],
                    ),
                    SizedBox(height: 8),
                    ElevatedButton(
                      onPressed: isLoading
                          ? null
                          : () {
                              _switchDiagramType(selectedDiagramType,
                                  forceRedraw: true);
                            },
                      child: Text('Yeniden Çiz'),
                    ),
                  ],
                ),
              ),
            ),
          ],

          SizedBox(height: 16),

          // Error Message
          if (errorMessage != null)
            Container(
              padding: EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: Colors.red.withOpacity(0.1),
                borderRadius: BorderRadius.circular(8),
                border: Border.all(color: Colors.red.shade300),
              ),
              child: Row(
                children: [
                  Icon(Icons.error, color: Colors.red),
                  SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      errorMessage!,
                      style: TextStyle(color: Colors.red.shade700),
                    ),
                  ),
                ],
              ),
            ),

          if (errorMessage != null) SizedBox(height: 16),

          // Loading Indicator
          if (isLoading)
            Container(
              height: 300,
              child: Center(
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    CircularProgressIndicator(),
                    SizedBox(height: 16),
                    Text('Diagram oluşturuluyor...'),
                  ],
                ),
              ),
            )
          else
            // Diagram Display
            Expanded(
              child: Card(
                child: Container(
                  width: double.infinity,
                  padding: EdgeInsets.all(16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      // Diagram Info
                      Row(
                        children: [
                          Icon(
                            selectedDiagramType == 'isothermal'
                                ? Icons.thermostat
                                : Icons.trending_up,
                            color: Colors.blue,
                          ),
                          SizedBox(width: 8),
                          Text(
                            selectedDiagramType == 'isothermal'
                                ? 'Isothermal Diagram'
                                : 'Vertical Section',
                            style: TextStyle(
                              fontWeight: FontWeight.bold,
                              fontSize: 16,
                            ),
                          ),
                        ],
                      ),

                      SizedBox(height: 8),

                      // System Info
                      if (currentDiagramData != null &&
                          currentDiagramData!.containsKey('system_info'))
                        Text(
                          'System: ${currentDiagramData!['system_info']}',
                          style: TextStyle(
                            fontStyle: FontStyle.italic,
                            color: Colors.grey.shade600,
                          ),
                        ),

                      SizedBox(height: 16),

                      // Diagram Image
                      Expanded(
                        child: currentDiagramData != null &&
                                currentDiagramData!
                                    .containsKey('diagram_base64')
                            ? Container(
                                width: double.infinity,
                                decoration: BoxDecoration(
                                  border:
                                      Border.all(color: Colors.grey.shade300),
                                  borderRadius: BorderRadius.circular(8),
                                ),
                                child: ClipRRect(
                                  borderRadius: BorderRadius.circular(8),
                                  child: Image.memory(
                                    base64Decode(
                                        currentDiagramData!['diagram_base64']),
                                    fit: BoxFit.contain,
                                    errorBuilder: (context, error, stackTrace) {
                                      return Container(
                                        height: 200,
                                        child: Center(
                                          child: Column(
                                            mainAxisAlignment:
                                                MainAxisAlignment.center,
                                            children: [
                                              Icon(Icons.error,
                                                  size: 48, color: Colors.red),
                                              SizedBox(height: 8),
                                              Text('Diagram yüklenemedi'),
                                            ],
                                          ),
                                        ),
                                      );
                                    },
                                  ),
                                ),
                              )
                            : Container(
                                height: 200,
                                decoration: BoxDecoration(
                                  border:
                                      Border.all(color: Colors.grey.shade300),
                                  borderRadius: BorderRadius.circular(8),
                                ),
                                child: Center(
                                  child: Text(
                                    'Diagram verisi bulunamadı',
                                    style:
                                        TextStyle(color: Colors.grey.shade600),
                                  ),
                                ),
                              ),
                      ),

                      SizedBox(height: 16),

                      // Stable Phases Info
                      if (currentDiagramData != null &&
                          currentDiagramData!.containsKey('stable_phases') &&
                          currentDiagramData!['stable_phases'] != null)
                        Container(
                          padding: EdgeInsets.all(12),
                          decoration: BoxDecoration(
                            color: Colors.green.withOpacity(0.1),
                            borderRadius: BorderRadius.circular(8),
                            border: Border.all(color: Colors.green.shade300),
                          ),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Row(
                                children: [
                                  Icon(Icons.check_circle,
                                      color: Colors.green, size: 20),
                                  SizedBox(width: 8),
                                  Text(
                                    'Kararlı Fazlar:',
                                    style: TextStyle(
                                      fontWeight: FontWeight.bold,
                                      color: Colors.green.shade700,
                                    ),
                                  ),
                                ],
                              ),
                              SizedBox(height: 8),
                              Wrap(
                                spacing: 8,
                                runSpacing: 4,
                                children: (currentDiagramData!['stable_phases']
                                        as List)
                                    .map<Widget>((phase) => Container(
                                          padding: EdgeInsets.symmetric(
                                            horizontal: 8,
                                            vertical: 4,
                                          ),
                                          decoration: BoxDecoration(
                                            color: Colors.green.shade100,
                                            borderRadius:
                                                BorderRadius.circular(4),
                                          ),
                                          child: Text(
                                            phase.toString(),
                                            style: TextStyle(
                                              fontSize: 12,
                                              fontWeight: FontWeight.w500,
                                            ),
                                          ),
                                        ))
                                    .toList(),
                              ),
                            ],
                          ),
                        ),
                    ],
                  ),
                ),
              ),
            ),
        ],
      ),
    );
  }
}
