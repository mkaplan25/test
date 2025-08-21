import 'dart:convert';
import 'dart:typed_data';
import 'package:flutter/material.dart';

class BinaryPhaseDisplay extends StatefulWidget {
  final Map<String, dynamic> result;

  const BinaryPhaseDisplay({
    super.key,
    required this.result,
  });

  @override
  State<BinaryPhaseDisplay> createState() => _BinaryPhaseDisplayState();
}

class _BinaryPhaseDisplayState extends State<BinaryPhaseDisplay> {
  TransformationController _transformationController =
      TransformationController();

  @override
  void dispose() {
    _transformationController.dispose();
    super.dispose();
  }

  void _resetZoom() {
    _transformationController.value = Matrix4.identity();
  }

  @override
  Widget build(BuildContext context) {
    final String? diagramBase64 = widget.result['diagram_base64'];
    final String elementPair =
        widget.result['element_pair'] ?? 'Binary Phase Diagram';
    final String xAxisLabel = widget.result['x_axis_label'] ?? 'Composition';
    final String yAxisLabel = widget.result['y_axis_label'] ?? 'Temperature';
    final bool success = widget.result['success'] ?? false;
    final String message = widget.result['message'] ?? '';

    return Padding(
      padding: const EdgeInsets.all(16.0),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Header
          Row(
            children: [
              Icon(Icons.scatter_plot, size: 24, color: Colors.blue[700]),
              SizedBox(width: 8),
              Text(
                elementPair,
                style: TextStyle(
                  fontSize: 20,
                  fontWeight: FontWeight.bold,
                  color: Colors.blue[700],
                ),
              ),
              Spacer(),
              IconButton(
                onPressed: _resetZoom,
                icon: Icon(Icons.zoom_out_map),
                tooltip: 'Reset Zoom',
              ),
            ],
          ),

          SizedBox(height: 8),

          // Axis labels
          Container(
            padding: EdgeInsets.all(8),
            decoration: BoxDecoration(
              color: Colors.grey[100],
              borderRadius: BorderRadius.circular(8),
            ),
            child: Row(
              children: [
                Expanded(
                  child: Text(
                    'X Axis: $xAxisLabel',
                    style: TextStyle(fontSize: 14, fontWeight: FontWeight.w500),
                  ),
                ),
                SizedBox(width: 16),
                Expanded(
                  child: Text(
                    'Y Axis: $yAxisLabel',
                    style: TextStyle(fontSize: 14, fontWeight: FontWeight.w500),
                  ),
                ),
              ],
            ),
          ),

          SizedBox(height: 16),

          // Status message
          if (message.isNotEmpty)
            Container(
              padding: EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: success ? Colors.green.shade50 : Colors.red.shade50,
                borderRadius: BorderRadius.circular(8),
                border: Border.all(
                  color: success ? Colors.green.shade300 : Colors.red.shade300,
                ),
              ),
              child: Row(
                children: [
                  Icon(
                    success ? Icons.check_circle : Icons.error,
                    color:
                        success ? Colors.green.shade600 : Colors.red.shade600,
                    size: 20,
                  ),
                  SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      message,
                      style: TextStyle(
                        color: success
                            ? Colors.green.shade700
                            : Colors.red.shade700,
                        fontWeight: FontWeight.w500,
                      ),
                    ),
                  ),
                ],
              ),
            ),

          SizedBox(height: 16),

          // Phase diagram display
          Expanded(
            child: Container(
              width: double.infinity,
              decoration: BoxDecoration(
                border: Border.all(color: Colors.grey.shade300),
                borderRadius: BorderRadius.circular(8),
              ),
              child: diagramBase64 != null
                  ? ClipRRect(
                      borderRadius: BorderRadius.circular(8),
                      child: InteractiveViewer(
                        transformationController: _transformationController,
                        boundaryMargin: EdgeInsets.all(20),
                        minScale: 0.5,
                        maxScale: 5.0,
                        child: Container(
                          width: double.infinity,
                          height: double.infinity,
                          child: Image.memory(
                            base64Decode(diagramBase64),
                            fit: BoxFit.contain,
                            errorBuilder: (context, error, stackTrace) {
                              return Center(
                                child: Column(
                                  mainAxisAlignment: MainAxisAlignment.center,
                                  children: [
                                    Icon(
                                      Icons.broken_image,
                                      size: 64,
                                      color: Colors.grey[400],
                                    ),
                                    SizedBox(height: 16),
                                    Text(
                                      'Diyagram görüntülenemiyor',
                                      style: TextStyle(
                                        color: Colors.grey[600],
                                        fontSize: 16,
                                      ),
                                    ),
                                    SizedBox(height: 8),
                                    Text(
                                      'Hata: $error',
                                      style: TextStyle(
                                        color: Colors.grey[500],
                                        fontSize: 12,
                                      ),
                                      textAlign: TextAlign.center,
                                    ),
                                  ],
                                ),
                              );
                            },
                          ),
                        ),
                      ),
                    )
                  : Center(
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Icon(
                            Icons.image_not_supported,
                            size: 64,
                            color: Colors.grey[400],
                          ),
                          SizedBox(height: 16),
                          Text(
                            'Faz diyagramı mevcut değil',
                            style: TextStyle(
                              color: Colors.grey[600],
                              fontSize: 16,
                            ),
                          ),
                        ],
                      ),
                    ),
            ),
          ),

          SizedBox(height: 16),

          // Controls info
          Container(
            padding: EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: Colors.blue.shade50,
              borderRadius: BorderRadius.circular(8),
              border: Border.all(color: Colors.blue.shade200),
            ),
            child: Row(
              children: [
                Icon(Icons.info, color: Colors.blue.shade600, size: 20),
                SizedBox(width: 8),
                Expanded(
                  child: Text(
                    'Diyagramı büyütmek için pinch-to-zoom kullanın. Kaydırmak için sürükleyin.',
                    style: TextStyle(
                      color: Colors.blue.shade700,
                      fontSize: 13,
                    ),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
