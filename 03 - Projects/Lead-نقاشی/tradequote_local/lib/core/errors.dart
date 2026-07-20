/// App exceptions carry a plain-language message safe to show the user
/// (tone rules: what happened → your work is safe → what to do next).
class AppException implements Exception {
  const AppException(this.userMessage, [this.technicalDetail]);

  final String userMessage;
  final String? technicalDetail;

  @override
  String toString() => 'AppException: $userMessage'
      '${technicalDetail == null ? '' : ' ($technicalDetail)'}';
}

class PaymentException extends AppException {
  const PaymentException(super.userMessage);
}

class OverpaymentException extends PaymentException {
  const OverpaymentException(this.balanceCents)
      : super('This is more than the amount still owing.');

  final int balanceCents;
}

class BackupException extends AppException {
  const BackupException(super.userMessage, [super.technicalDetail]);
}

class AiUnavailableException extends AppException {
  const AiUnavailableException()
      : super('This feature is not available right now. '
            'You can enter the information manually.');
}
