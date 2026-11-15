#include "adbmanager.h"

#include <QCoreApplication>
#include <QDir>
#include <QFileInfo>
#include <QRegularExpression>

#include <functional>

namespace {
QString packageDirectoryName()
{
#if defined(Q_OS_WIN)
    return QStringLiteral("platform-tools(Windows)");
#elif defined(Q_OS_MACOS)
    return QStringLiteral("Mac");
#else
    return QStringLiteral("platform-tools");
#endif
}

QString executableName()
{
#if defined(Q_OS_WIN)
    return QStringLiteral("adb.exe");
#else
    return QStringLiteral("adb");
#endif
}

QString findAdb()
{
    const QString package = packageDirectoryName();
    const QStringList roots = {
        QCoreApplication::applicationDirPath(),
        QDir::currentPath(),
        QDir(QCoreApplication::applicationDirPath()).absoluteFilePath(QStringLiteral("..")),
        QDir(QDir::currentPath()).absoluteFilePath(QStringLiteral(".."))
    };

    for (const QString& root : roots) {
        const QString path = QDir(root).absoluteFilePath(package + QDir::separator() + executableName());
        if (QFileInfo::exists(path) && QFileInfo(path).isFile())
            return QDir::cleanPath(path);
    }
    return {};
}
}

AdbManager::AdbManager(QObject* parent) : QObject(parent), m_adbPath(findAdb())
{
    if (m_adbPath.isEmpty())
        setError(QStringLiteral("No host-matched ADB executable was found for %1.").arg(hostPlatformName()));
}

QString AdbManager::adbPath() const { return m_adbPath; }

QString AdbManager::hostPlatformName() const
{
#if defined(Q_OS_WIN)
    return QStringLiteral("Windows");
#elif defined(Q_OS_MACOS)
    return QStringLiteral("macOS");
#elif defined(Q_OS_LINUX)
    return QStringLiteral("Linux");
#else
    return QStringLiteral("unsupported host");
#endif
}

QString AdbManager::lastError() const { return m_lastError; }
QVector<AdbDevice> AdbManager::devices() const { return m_devices; }

void AdbManager::setError(const QString& message)
{
    m_lastError = message;
    emit errorMessage(message);
}

void AdbManager::run(const QStringList& arguments,
                     std::function<void(const QByteArray&, const QByteArray&, int)> finished)
{
    if (m_adbPath.isEmpty()) {
        setError(m_lastError.isEmpty() ? QStringLiteral("ADB executable is unavailable.") : m_lastError);
        return;
    }
    if (m_process) {
        setError(QStringLiteral("ADB is busy; please wait for the current operation to finish."));
        return;
    }

    m_process = new QProcess(this);
    m_process->setProgram(m_adbPath);
    m_process->setArguments(arguments);
    m_process->setProcessChannelMode(QProcess::SeparateChannels);
    emit operationBusy(true);
    connect(m_process, &QProcess::errorOccurred, this, [this](QProcess::ProcessError) {
        setError(QStringLiteral("ADB process error: %1").arg(m_process ? m_process->errorString() : QString()));
    });
    connect(m_process, qOverload<int, QProcess::ExitStatus>(&QProcess::finished), this,
            [this, finished](int code, QProcess::ExitStatus) {
                QProcess* process = m_process;
                const QByteArray out = process->readAllStandardOutput();
                const QByteArray err = process->readAllStandardError();
                m_process = nullptr;
                emit operationBusy(false);
                process->deleteLater();
                finished(out, err, code);
            });
    m_process->start();
}

void AdbManager::checkVersion()
{
    run({QStringLiteral("version")}, [this](const QByteArray& out, const QByteArray& err, int code) {
        if (code != 0) {
            setError(QStringLiteral("ADB version check failed: %1").arg(QString::fromLocal8Bit(err).trimmed()));
            return;
        }
        const QString text = QString::fromLocal8Bit(out).trimmed();
        emit versionDetected(text);
        emit statusMessage(QStringLiteral("ADB ready: %1").arg(text.split('\n').value(1, text).trimmed()));
    });
}

void AdbManager::startServer()
{
    run({QStringLiteral("start-server")}, [this](const QByteArray&, const QByteArray& err, int code) {
        if (code != 0) {
            setError(QStringLiteral("Could not start ADB server: %1").arg(QString::fromLocal8Bit(err).trimmed()));
            return;
        }
        emit statusMessage(QStringLiteral("ADB server started."));
        refreshDevices();
    });
}

void AdbManager::stopServer()
{
    run({QStringLiteral("kill-server")}, [this](const QByteArray&, const QByteArray& err, int code) {
        if (code != 0) {
            setError(QStringLiteral("Could not stop ADB server: %1").arg(QString::fromLocal8Bit(err).trimmed()));
            return;
        }
        m_devices.clear();
        emit devicesUpdated(m_devices);
        emit statusMessage(QStringLiteral("ADB server stopped."));
    });
}

void AdbManager::refreshDevices()
{
    run({QStringLiteral("devices"), QStringLiteral("-l")}, [this](const QByteArray& out, const QByteArray& err, int code) {
        if (code != 0) {
            setError(QStringLiteral("Could not list devices: %1").arg(QString::fromLocal8Bit(err).trimmed()));
            return;
        }

        QVector<AdbDevice> parsed;
        const QStringList lines = QString::fromLocal8Bit(out).split(QRegularExpression(QStringLiteral("[\\r\\n]+")), Qt::SkipEmptyParts);
        for (const QString& line : lines) {
            if (line.startsWith(QStringLiteral("List of devices")))
                continue;
            const QStringList fields = line.split(QRegularExpression(QStringLiteral("\\s+")), Qt::SkipEmptyParts);
            if (fields.size() < 2)
                continue;
            AdbDevice device;
            device.serial = fields.at(0);
            device.state = fields.at(1);
            for (int i = 2; i < fields.size(); ++i) {
                const auto pair = fields.at(i).split('=', Qt::KeepEmptyParts);
                if (pair.size() != 2)
                    continue;
                if (pair.at(0) == QStringLiteral("model")) device.model = pair.at(1);
                if (pair.at(0) == QStringLiteral("product")) device.product = pair.at(1);
                if (pair.at(0) == QStringLiteral("transport_id")) device.transport = pair.at(1);
            }
            parsed.append(device);
        }
        m_devices = parsed;
        emit devicesUpdated(m_devices);
        emit statusMessage(QStringLiteral("Detected %1 device(s).").arg(m_devices.size()));
    });
}

void AdbManager::connectWireless(const QString& hostPort)
{
    const QString target = hostPort.trimmed();
    if (target.isEmpty()) {
        setError(QStringLiteral("Wireless connection requires a host and port."));
        return;
    }
    run({QStringLiteral("connect"), target}, [this, target](const QByteArray& out, const QByteArray& err, int code) {
        const QString message = QString::fromLocal8Bit(code == 0 ? out : err).trimmed();
        if (code != 0) {
            setError(QStringLiteral("Could not connect to %1: %2").arg(target, message));
            return;
        }
        emit statusMessage(message.isEmpty() ? QStringLiteral("Connected to %1.").arg(target) : message);
        refreshDevices();
    });
}

void AdbManager::pairWireless(const QString& hostPort, const QString& pairingCode)
{
    const QString target = hostPort.trimmed();
    const QString codeText = pairingCode.trimmed();
    if (target.isEmpty() || codeText.isEmpty()) {
        setError(QStringLiteral("Wireless pairing requires a host, port, and pairing code."));
        return;
    }
    run({QStringLiteral("pair"), target, codeText}, [this, target](const QByteArray& out, const QByteArray& err, int code) {
        const QString message = QString::fromLocal8Bit(code == 0 ? out : err).trimmed();
        if (code != 0) {
            setError(QStringLiteral("Could not pair with %1: %2").arg(target, message));
            return;
        }
        emit statusMessage(message.isEmpty() ? QStringLiteral("Paired with %1.").arg(target) : message);
    });
}

void AdbManager::disconnectDevice(const QString& serial)
{
    const QString target = serial.trimmed();
    if (target.isEmpty()) {
        setError(QStringLiteral("Disconnect requires a device serial or host:port."));
        return;
    }
    run({QStringLiteral("disconnect"), target}, [this, target](const QByteArray& out, const QByteArray& err, int code) {
        const QString message = QString::fromLocal8Bit(code == 0 ? out : err).trimmed();
        if (code != 0) {
            setError(QStringLiteral("Could not disconnect %1: %2").arg(target, message));
            return;
        }
        emit statusMessage(message.isEmpty() ? QStringLiteral("Disconnected %1.").arg(target) : message);
        refreshDevices();
    });
}
