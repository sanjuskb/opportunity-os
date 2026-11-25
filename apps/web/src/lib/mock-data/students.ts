import type { StudentProfile } from '@opportunity-os/shared-types';

export interface VerifiedCredential {
  id: string;
  title: string;
  issuer: string;
  verificationSource: 'AICTE' | 'UGC' | 'NPTEL' | 'GitHub' | 'University Registrar';
  issueDate: string;
  verificationHash: string;
  gradeOrScore?: string;
  credentialUrl: string;
}

export interface StudentFullData extends StudentProfile {
  headline: string;
  about: string;
  atsScore: number;
  careerPassportId: string;
  avatarUrl: string;
  verifiedCredentials: VerifiedCredential[];
  projects: {
    title: string;
    description: string;
    technologies: string[];
    githubUrl?: string;
    liveUrl?: string;
    verifiedCommitHash?: string;
  }[];
}

export const CURRENT_STUDENT: StudentFullData = {
  id: 'std-sanju-01',
  userId: 'usr-sanju-01',
  fullName: 'Sanju S. Kumar',
  headline: 'AI Systems Engineer & Full-Stack Architect',
  email: 'sanju.kumar@college.edu.in',
  phone: '+91 98765 43210',
  collegeName: 'National Institute of Technology (NIT), Tiruchirappalli',
  degree: 'B.Tech',
  branch: 'Computer Science and Engineering',
  graduationYear: 2026,
  cgpa: 8.82,
  state: 'Tamil Nadu',
  preferredLanguage: 'en',
  skills: [
    'Python',
    'PyTorch',
    'TypeScript',
    'Next.js',
    'React',
    'Tailwind CSS',
    'FastAPI',
    'Transformers',
    'PostgreSQL',
    'Docker',
    'WebSockets',
  ],
  atsScore: 94,
  careerPassportId: 'PASSPORT-IN-2026-NIT-8820',
  avatarUrl: 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=256&h=256&q=80',
  about:
    'Third-year undergraduate student focused on voice-first Indic AI applications, agentic orchestrators, and high-performance WebGL interfaces. Core engineering contributor to NexteRaS (Team SyNtRax).',
  createdAt: '2026-09-01T00:00:00Z',
  updatedAt: '2026-11-23T18:00:00Z',
  verifiedCredentials: [
    {
      id: 'cred-aicte-01',
      title: 'B.Tech Computer Science & Engineering (UGC Approved)',
      issuer: 'National Institute of Technology, Tiruchirappalli',
      verificationSource: 'AICTE',
      issueDate: '2023-08-10',
      verificationHash: '0x8f2a991bce47101a884ef',
      gradeOrScore: '8.82 CGPA (Current)',
      credentialUrl: 'https://digilocker.gov.in/verify/0x8f2a991bce47101a884ef',
    },
    {
      id: 'cred-nptel-02',
      title: 'Deep Learning & Natural Language Processing',
      issuer: 'NPTEL (IIT Madras)',
      verificationSource: 'NPTEL',
      issueDate: '2025-05-15',
      verificationHash: '0x3c990aa41d6b8290',
      gradeOrScore: 'Elite + Gold (92%)',
      credentialUrl: 'https://nptel.ac.in/noc/verify/0x3c990aa41d6b8290',
    },
    {
      id: 'cred-gh-03',
      title: 'NexteRaS Autonomous Platform Contributor',
      issuer: 'GitHub Verified Commits',
      verificationSource: 'GitHub',
      issueDate: '2026-11-23',
      verificationHash: '0xff0bfd2242d24',
      gradeOrScore: 'Verified Committer',
      credentialUrl: 'https://github.com/sanjuskb/opportunity-os',
    },
  ],
  projects: [
    {
      title: 'NexteRaS — AI Career Intelligence & Autonomous Employability System',
      description:
        'Architected an autonomous career intelligence operating system for Indian students with 7-language speech support, R3F 3D architectural campus, and deterministic eligibility validation.',
      technologies: ['Next.js 15', 'React 19', 'React Three Fiber', 'FastAPI', 'LangGraph', 'Tailwind CSS'],
      githubUrl: 'https://github.com/sanjuskb/opportunity-os',
      verifiedCommitHash: '0ff0bfd',
    },
    {
      title: 'Indic-Transcribe: Low-Latency Regional Speech Recognition',
      description:
        'Fine-tuned multilingual Conformer models on Common Voice Telugu and Tamil datasets, achieving 14.2% WER under edge constraints.',
      technologies: ['Python', 'PyTorch', 'Hugging Face', 'Web Audio API'],
      githubUrl: 'https://github.com/sanjuskb/indic-transcribe',
    },
  ],
};

export const MOCK_CANDIDATES: StudentFullData[] = [
  CURRENT_STUDENT,
  {
    id: 'std-ananya-02',
    userId: 'usr-ananya-02',
    fullName: 'Ananya Sharma',
    headline: 'Distributed Systems & Cloud Infrastructure Specialist',
    email: 'ananya.s@iiit.ac.in',
    phone: '+91 99887 76655',
    collegeName: 'IIIT Hyderabad',
    degree: 'B.Tech',
    branch: 'Computer Science',
    graduationYear: 2025,
    cgpa: 9.15,
    state: 'Telangana',
    preferredLanguage: 'te',
    skills: ['Go', 'Rust', 'Kubernetes', 'Docker', 'Distributed Systems', 'gRPC', 'PostgreSQL'],
    atsScore: 97,
    careerPassportId: 'PASSPORT-IN-2025-IIITH-9150',
    avatarUrl: 'https://images.unsplash.com/photo-1494790108377-be9c29b29330?auto=format&fit=crop&w=256&h=256&q=80',
    about: 'Final-year student specializing in high-throughput cloud storage engines and Paxos consensus protocols.',
    createdAt: '2026-08-15T00:00:00Z',
    updatedAt: '2026-11-20T10:00:00Z',
    verifiedCredentials: [
      {
        id: 'cred-iiit-01',
        title: 'B.Tech Honors in Computer Science',
        issuer: 'IIIT Hyderabad',
        verificationSource: 'University Registrar',
        issueDate: '2025-06-01',
        verificationHash: '0x99aab3312bc',
        gradeOrScore: '9.15 CGPA',
        credentialUrl: 'https://iiit.ac.in/verify',
      },
    ],
    projects: [
      {
        title: 'Raft-KV: Distributed Sharded Key-Value Store',
        description: 'Implemented Raft consensus in Go with zero data loss under simulated network partitions.',
        technologies: ['Go', 'Raft', 'gRPC', 'Prometheus'],
        githubUrl: 'https://github.com/ananya/raft-kv',
      },
    ],
  },
  {
    id: 'std-rahul-03',
    userId: 'usr-rahul-03',
    fullName: 'Rahul Verma',
    headline: 'Computer Vision & Embedded ML Engineer',
    email: 'rahul.verma@iitm.ac.in',
    phone: '+91 97766 55443',
    collegeName: 'IIT Madras',
    degree: 'Dual Degree (B.Tech + M.Tech)',
    branch: 'Data Science & Engineering',
    graduationYear: 2026,
    cgpa: 8.94,
    state: 'Tamil Nadu',
    preferredLanguage: 'hi',
    skills: ['Python', 'C++', 'OpenCV', 'PyTorch', 'ROS', 'CUDA', 'TensorRT'],
    atsScore: 92,
    careerPassportId: 'PASSPORT-IN-2026-IITM-8940',
    avatarUrl: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?auto=format&fit=crop&w=256&h=256&q=80',
    about: 'Researcher in real-time embedded vision models for robotics and edge drones.',
    createdAt: '2026-07-10T00:00:00Z',
    updatedAt: '2026-11-22T14:00:00Z',
    verifiedCredentials: [
      {
        id: 'cred-iitm-01',
        title: 'Institute Merit Scholar',
        issuer: 'IIT Madras',
        verificationSource: 'University Registrar',
        issueDate: '2024-04-12',
        verificationHash: '0x77eeff221aa',
        credentialUrl: 'https://iitm.ac.in',
      },
    ],
    projects: [
      {
        title: 'EdgeYOLO: 60 FPS Quantized Detection on Raspberry Pi',
        description: 'INT8 quantized real-time object detection using TensorRT and ONNX runtime.',
        technologies: ['C++', 'TensorRT', 'Python', 'ONNX'],
      },
    ],
  },
];
